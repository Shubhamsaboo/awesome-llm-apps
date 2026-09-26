"""Deterministic regressions. All model responses here are controlled fixtures."""
import asyncio, base64, io, json, sys, time, unittest, zipfile
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import policies as p
from agent import blank_claim, build_initial_workflow_state
from schemas import ClaimNarrative
from policy_directory import lookup_policy
from live_demo import server as s
from fastapi.testclient import TestClient


def claim(**updates):
    c = blank_claim()
    c.update(policyholder_name='Maya Singh', policy_number='H0-44721', contact_method='maya@example.com', date_of_loss='2026-09-17', reported_date='2026-09-18', loss_location='Test room', loss_description='A pipe burst and damaged the floor.', raw_narrative_summary='Pipe burst.', estimated_loss_usd=2000)
    c.update(updates)
    return c


def workflow(c, kind='home_water_damage'):
    cls = dict(claim_type=kind, severity='medium', severity_rationale='Test fixture', likely_policy_line='Test', loss_drivers=[], claimant_needs=[])
    v = p.validate_required_claim_fields(c)
    cov = p.apply_coverage_and_evidence_rules(c,v,cls)
    docs = p.generate_document_checklist(c,cls,cov)
    gate = p.fraud_signal_and_safety_gate(c,v,cls,cov)
    packet = p.build_claim_intake_packet(c,v,cls,cov,docs,gate)
    return dict(normalized_claim=c, claim_classification=cls, field_validation=v, coverage_evidence_decision=cov, document_checklist=docs, fraud_safety_gate=gate, claim_intake_packet=packet)


def route(w):
    return w['fraud_safety_gate']['final_routing_decision']


class DomainTests(unittest.TestCase):
    def test_negated_documents_never_count_as_received(self):
        c=claim(loss_description='I have no photos, no receipts, and no repair estimate.', documents_mentioned=['no photos', 'no receipts'])
        w=workflow(c)
        self.assertEqual(route(w),'needs_docs')
        self.assertFalse(any(d['already_provided'] for d in w['document_checklist']['items']))

    def test_future_and_available_documents_stay_outstanding(self):
        for status in ['missing','planned','available','unknown']:
            with self.subTest(status=status):
                w=workflow(claim(evidence_records=[dict(document_type='damage_photo',status=status)]))
                photo=w['document_checklist']['items'][0]
                self.assertFalse(photo['already_provided']); self.assertEqual(photo['status'],status)

    def test_model_cannot_mint_received_evidence(self):
        c=p.prepare_claim(claim(evidence_records=[dict(document_type='damage_photo',status='received',evidence_ids=['invented'])]))
        self.assertEqual(c['evidence_records'][0]['status'],'available')
        self.assertEqual(c['evidence_records'][0]['evidence_ids'],[])

    def test_capture_only_satisfies_exact_document_type(self):
        c=p.prepare_claim(claim(),[dict(id='real1',document_types=['damage_photo'])])
        items=workflow(c)['document_checklist']['items']
        self.assertEqual([x['item'] for x in items if x['already_provided']],['Photos or video of damaged areas before cleanup'])
        self.assertEqual(items[0]['evidence_ids'],['real1'])

    def test_all_actual_documents_can_complete_packet(self):
        c=p.prepare_claim(claim(),[dict(id='capture-'+t, document_types=[t]) for t in ['damage_photo','drying_invoice','repair_estimate','ownership_receipt']])
        self.assertEqual(route(workflow(c)),'ready_for_adjuster')

    def test_safety_negations(self):
        for text in ['No one is hurt.', 'There is no mold and no electrical hazard.', 'No one was injured.', 'No injuries or safety concerns.', 'I am not in pain.']:
            with self.subTest(text=text):
                self.assertNotEqual(route(workflow(claim(loss_description=text,raw_narrative_summary=''))),'emergency_escalation')

    def test_safety_all_claim_categories(self):
        for kind in ['home_water_damage','auto_collision','other','travel_delay_cancellation']:
            with self.subTest(kind=kind):
                self.assertEqual(route(workflow(claim(safety_facts=[dict(category='injury',status='present',description='Claimant injured')]),kind)),'emergency_escalation')

    def test_safety_negation_does_not_hide_other_hazard(self):
        for text in ['No injuries, but there is exposed electrical wiring in water.', 'We have no place to live.', 'The house is not safe.']:
            with self.subTest(text=text):
                self.assertEqual(route(workflow(claim(loss_description=text,raw_narrative_summary=''))),'emergency_escalation')

    def test_latest_safety_correction_overrides_legacy_text(self):
        c=claim(loss_description='Earlier an injury was reported.',safety_facts=[dict(category='injury',status='absent',description='Correction: nobody is injured')])
        self.assertNotEqual(route(workflow(c)),'emergency_escalation')

    def test_high_loss_negative_evidence_does_not_bypass_gate(self):
        w=workflow(claim(estimated_loss_usd=20000,documents_mentioned=['no receipts'],evidence_records=[dict(document_type='ownership_receipt',status='missing')]))
        self.assertIn('EVID-001',[x['signal_id'] for x in w['fraud_safety_gate']['signals']])

    def test_invalid_dates_block(self):
        for value in ['banana','2026-02-30','2099-01-01','2026-09-17 until later']:
            with self.subTest(value=value):
                self.assertEqual(p.validate_required_claim_fields(claim(date_of_loss=value))['intake_status'],'missing_info')

    def test_invalid_loss_amounts_rejected(self):
        for value in [-5,float('nan'),float('inf')]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                ClaimNarrative.model_validate(claim(estimated_loss_usd=value))

    def test_policy_corrections_update_and_clear_record(self):
        session=s.IntakeSession('test',policy_record=lookup_policy('H0-44721'))
        for number in ['AUTO-11111','NOT-FOUND','not specified']:
            s._attach_policy_from_claim(session, workflow(claim(policy_number=number)))
            if number=='not specified': self.assertIsNone(session.policy_record)
            else: self.assertEqual(session.policy_record['policy_number'],number)

    def test_policy_review_routes(self):
        for kwargs in [dict(policy_number='NOT-FOUND'),dict(policy_number='AUTO-11111',policyholder_name='Chris Park'),dict(policy_number='AUTO-90210',policyholder_name='Jordan Lee'),dict(policyholder_name='Someone Else')]:
            with self.subTest(kwargs=kwargs): self.assertEqual(route(workflow(claim(**kwargs))),'policy_review')

    def test_policy_period_uses_loss_not_current_date(self):
        self.assertEqual(route(workflow(claim(policy_number='AUTO-90210',policyholder_name='Jordan Lee',date_of_loss='2026-09-14'))),'needs_docs')

    def test_dialogue_retains_questions_and_ids(self):
        session=s.IntakeSession('test')
        s.append_turn(session,'Agent','Are you injured?','q1')
        s.append_turn(session,'Claimant','No.','a1')
        s.append_turn(session,'Agent','Do you have photos?','q2')
        s.append_turn(session,'Claimant','Yes.','a2')
        text=s._claimant_text(session)
        self.assertIn('[q1] Agent: Are you injured?',text)
        self.assertIn('[a2] Claimant: Yes.',text)

    def test_agent_reply_does_not_trigger_duplicate_claim_extraction(self):
        session=s.IntakeSession('revision')
        s.append_turn(session,'Claimant','The pipe burst','u1')
        revision=session.revision
        s.append_turn(session,'Agent','Do you have photos?','a1')
        self.assertEqual(session.revision,revision)
        self.assertIn('Do you have photos?',s._intake_text(session))

    def test_turn_retry_deduplicates_only_identifier(self):
        session=s.IntakeSession('test')
        s.append_turn(session,'Claimant','No injuries','1');s.append_turn(session,'Claimant','No','2');s.append_turn(session,'Claimant','No','2')
        self.assertEqual(len(session.transcript),2)

    def test_empty_progress_and_missing_photos(self):
        ui=s._state_from_workflow(s.IntakeSession('test'),build_initial_workflow_state())
        self.assertEqual(ui['progress'],0)
        self.assertEqual(ui['fields']['photos']['status'],'missing')

    def test_progress_only_applicable_fields_and_received_docs(self):
        ui=s._state_from_workflow(s.IntakeSession('test'),workflow(claim()))
        self.assertEqual(ui['progress'],60)


class AsyncTests(unittest.IsolatedAsyncioTestCase):
    async def test_exact_frozen_frame_reverified_despite_new_arrival(self):
        session=s.IntakeSession('frame',last_frame=b'FRAME_A',last_frame_id='a',last_frame_at=time.monotonic())
        async def model(**kwargs):
            self.assertEqual(kwargs['contents'][0].inline_data.data,b'FRAME_A')
            session.last_frame=b'FRAME_B'
            return NS(text=json.dumps(dict(observation='Blank wall',supports_claimant_description=False,document_types=[])))
        with patch.object(s,'_client',return_value=NS(aio=NS(models=NS(generate_content=model)))):
            result=await s._pin_evidence_photo(session,dict(observation='Huge crack',confirmed=True,claimant_description='A crack'))
        photo=session.evidence_photos[0]
        self.assertEqual(base64.b64decode(photo['data_url'].split(',')[1]),b'FRAME_A')
        self.assertEqual(photo['caption'],'Blank wall')
        self.assertFalse(result['confirmed']);self.assertIn('unconfirmed',session.camera_notes[0])

    async def test_without_claimant_description_capture_is_unconfirmed(self):
        session=s.IntakeSession('frame',last_frame=b'FRAME',last_frame_at=time.monotonic())
        async def model(**kwargs): return NS(text=json.dumps(dict(observation='Wall',supports_claimant_description=True,document_types=[])))
        with patch.object(s,'_client',return_value=NS(aio=NS(models=NS(generate_content=model)))):
            self.assertFalse((await s._pin_evidence_photo(session,{}))['confirmed'])
        self.assertIn('unconfirmed',session.camera_notes[0])

    async def test_stale_frames_and_photo_limits(self):
        session=s.IntakeSession('frame',last_frame=b'OLD',last_frame_at=time.monotonic()-30)
        self.assertFalse((await s._pin_evidence_photo(session,{}))['pinned'])
        session.last_frame_at=time.monotonic();session.evidence_photos=[{}]*s.MAX_PHOTOS
        self.assertFalse((await s._pin_evidence_photo(session,{}))['pinned'])

    async def test_older_sketch_cannot_overwrite_correction(self):
        session=s.IntakeSession('sketch')
        async def model(**kwargs):
            old='OLD_SCENE' in kwargs['contents'];await asyncio.sleep(.03 if old else .001)
            return NS(candidates=[NS(content=NS(parts=[NS(inline_data=NS(data=b'old' if old else b'new',mime_type='image/png'))]))])
        with patch.object(s,'_client',return_value=NS(aio=NS(models=NS(generate_content=model)))):
            results=await asyncio.gather(s._draw_incident_sketch(session,dict(scene_description='OLD_SCENE')),s._draw_incident_sketch(session,dict(scene_description='CORRECTED_SCENE')))
        self.assertEqual(session.sketch['brief'],'CORRECTED_SCENE');self.assertFalse(results[0]['sketched'])

    async def test_camera_on_blocks_automatic_sketch_without_model_call(self):
        session=s.IntakeSession('camera',camera_enabled=True)
        with patch.object(s,'_client') as client:
            result=await s._draw_incident_sketch(session,dict(scene_description='Kitchen with a burst pipe'))
        self.assertFalse(result['sketched']);client.assert_not_called()

    async def test_camera_off_defaults_to_automatic_sketch(self):
        session=s.IntakeSession('camera')
        async def model(**kwargs):
            return NS(candidates=[NS(content=NS(parts=[NS(inline_data=NS(data=b'sketch',mime_type='image/png'))]))])
        with patch.object(s,'_client',return_value=NS(aio=NS(models=NS(generate_content=model)))):
            result=await s._draw_incident_sketch(session,dict(scene_description='Kitchen with a burst pipe'))
        self.assertTrue(result['sketched']);self.assertEqual(session.sketch['trigger'],'automatic')

    async def test_explicit_sketch_and_corrections_work_with_camera_on(self):
        session=s.IntakeSession('camera',camera_enabled=True)
        async def model(**kwargs):
            return NS(candidates=[NS(content=NS(parts=[NS(inline_data=NS(data=b'sketch',mime_type='image/png'))]))])
        with patch.object(s,'_client',return_value=NS(aio=NS(models=NS(generate_content=model)))):
            for trigger,brief in [('explicit_request','Kitchen with sink on left'),('correction','Correction: sink on right')]:
                result=await s._draw_incident_sketch(session,dict(scene_description=brief,trigger=trigger))
                self.assertTrue(result['sketched'])
        self.assertEqual(session.sketch['version'],2)

    async def test_camera_toggle_discards_inflight_automatic_sketch(self):
        session=s.IntakeSession('camera')
        async def model(**kwargs):
            s.set_camera_mode(session,True)
            s.set_camera_mode(session,False)
            return NS(candidates=[NS(content=NS(parts=[NS(inline_data=NS(data=b'outdated',mime_type='image/png'))]))])
        with patch.object(s,'_client',return_value=NS(aio=NS(models=NS(generate_content=model)))):
            result=await s._draw_incident_sketch(session,dict(scene_description='Kitchen with a burst pipe'))
        self.assertFalse(result['sketched']);self.assertIsNone(session.sketch)

    async def test_camera_off_clears_live_frame_but_retains_pinned_photos(self):
        photo={'id':'pinned'}
        session=s.IntakeSession('camera',camera_enabled=True,last_frame=b'frame',last_frame_id='frame-id',last_frame_at=time.monotonic(),evidence_photos=[photo])
        s.set_camera_mode(session,False)
        self.assertFalse(session.camera_enabled);self.assertIsNone(session.last_frame)
        self.assertEqual(session.evidence_photos,[photo])
        self.assertFalse((await s._pin_evidence_photo(session,{}))['pinned'])

    async def test_unchanged_scene_reuses_existing_sketch(self):
        session=s.IntakeSession('camera',sketch={'brief':'Kitchen with a burst pipe','version':1})
        with patch.object(s,'_client') as client:
            result=await s._draw_incident_sketch(session,dict(scene_description='Kitchen with a burst pipe'))
        self.assertTrue(result['reused']);client.assert_not_called()

    async def test_missing_scene_or_nonexistent_correction_does_not_draw(self):
        for args in [{},dict(scene_description='Kitchen',trigger='correction')]:
            with patch.object(s,'_client') as client:
                result=await s._draw_incident_sketch(s.IntakeSession('camera'),args)
            self.assertFalse(result['sketched']);client.assert_not_called()

    async def test_camera_state_turns_inform_model_without_claimant_facts(self):
        session=s.IntakeSession('camera-wire',owner='owner');s.sessions[session.session_id]=session
        messages=[dict(type='camera_state',enabled=True),dict(type='camera_state',enabled=False),dict(type='close')]
        delivered=[]
        class WS:
            headers={'host':'127.0.0.1:4188','origin':'http://127.0.0.1:4188'}
            client=NS(host='127.0.0.1');url=NS(scheme='ws');cookies={'intake_owner':'owner'};query_params={'session_id':'camera-wire'}
            async def accept(self):pass
            async def close(self,**kw):pass
            async def send_json(self,payload):pass
            async def receive_text(self):return json.dumps(messages.pop(0))
        class Live:
            async def send_client_content(self,**kw):delivered.append(kw)
            async def receive(self):
                await asyncio.Event().wait()
                yield None
        class CM:
            async def __aenter__(self):return Live()
            async def __aexit__(self,*args):pass
        fake=NS(aio=NS(live=NS(connect=lambda **kw:CM())))
        with patch.object(s,'_has_api_key',return_value=True),patch.object(s,'_live_client',return_value=fake):
            await asyncio.wait_for(s.live_voice(WS()),1)
        self.assertEqual([x['turn_complete'] for x in delivered],[False,False])
        self.assertIn('STATE: ON',delivered[0]['turns'].parts[0].text)
        self.assertIn('STATE: OFF',delivered[1]['turns'].parts[0].text)
        self.assertEqual(session.transcript,[])
        s.sessions.pop(session.session_id)

    async def test_workflow_reruns_if_facts_change_in_flight(self):
        session=s.IntakeSession('race');s.append_turn(session,'Claimant','Original','one')
        calls=[]
        async def run(text,**kwargs):
            calls.append(text)
            if len(calls)==1: s.append_turn(session,'Claimant','Correction','two')
            return workflow(claim(loss_description='Correction' if len(calls)==2 else 'Original'))
        with patch.object(s,'run_claim_workflow',side_effect=run): result=await s._run_workflow_cached(session)
        self.assertEqual(len(calls),2);self.assertEqual(result['normalized_claim']['loss_description'],'Correction')

    async def test_cleanup_deletes_frames_and_cancels_jobs(self):
        session=s.IntakeSession('expired',updated_at=time.monotonic()-s.SESSION_TTL-1,last_frame=b'image',evidence_photos=[{}])
        job=asyncio.create_task(asyncio.sleep(100));session.tasks.add(job);s.sessions[session.session_id]=session
        await s.cleanup_sessions()
        self.assertNotIn('expired',s.sessions);self.assertTrue(job.cancelled());self.assertIsNone(session.last_frame);self.assertEqual(session.evidence_photos,[])

    async def test_slow_workflow_does_not_block_video_audio_or_close(self):
        session=s.IntakeSession('transport',owner='owner');s.sessions[session.session_id]=session
        started=asyncio.Event();media=[]
        class WS:
            headers={'host':'127.0.0.1:4188','origin':'http://127.0.0.1:4188'}
            client=NS(host='127.0.0.1');url=NS(scheme='ws');cookies={'intake_owner':'owner'};query_params={'session_id':'transport'}
            def __init__(self):self.i=0;self.sent=[]
            async def accept(self):pass
            async def close(self,**kw):pass
            async def send_json(self,payload):self.sent.append(payload)
            async def receive_text(self):
                messages=[dict(type='text',text='Test claim',id='1'),dict(type='video',data=base64.b64encode(b'\xff\xd8\xffTEST').decode()),dict(type='audio',data='AAA='),dict(type='close')]
                if self.i==1:await started.wait()
                value=messages[self.i];self.i+=1;return json.dumps(value)
        class Live:
            async def send_client_content(self,**kw):pass
            async def send_realtime_input(self,**kw):media.extend(kw)
            async def receive(self):
                await asyncio.Event().wait()
                yield None
        class CM:
            async def __aenter__(self):return Live()
            async def __aexit__(self,*args):pass
        async def run(*args,**kw):started.set();await asyncio.Event().wait()
        fake=NS(aio=NS(live=NS(connect=lambda **kw:CM())))
        with patch.object(s,'_has_api_key',return_value=True),patch.object(s,'_live_client',return_value=fake),patch.object(s,'run_claim_workflow',side_effect=run):
            ws=WS();await asyncio.wait_for(s.live_voice(ws),1)
        self.assertEqual(media,['video','audio']);self.assertFalse(session.camera_enabled);self.assertIsNone(session.live_socket);self.assertEqual(session.transcript[0]['id'],'1')
        s.sessions.pop('transport')


class AccessTests(unittest.TestCase):
    def setUp(self):
        s.sessions.clear();self.client=TestClient(s.app,base_url='http://127.0.0.1:4188');self.headers={'Origin':'http://127.0.0.1:4188'}
    def tearDown(self):self.client.close();s.sessions.clear()
    def create(self):return self.client.post('/api/sessions',headers=self.headers).json()['session_id']
    def test_owner_cookie_required(self):
        sid=self.create();self.assertEqual(self.client.get('/api/sessions/'+sid).status_code,200)
        with TestClient(s.app,base_url='http://127.0.0.1:4188') as other:
            self.assertEqual(other.get('/api/sessions/'+sid).status_code,404)
    def test_origin_host_and_missing_origin_rejected(self):
        for headers in [{},{'Origin':'https://evil.example'},{'Origin':'http://evil.example','Host':'evil.example'}]:
            self.assertEqual(self.client.post('/api/sessions',headers=headers).status_code,403)
    def test_websocket_rejects_origin_and_wrong_owner(self):
        from starlette.websockets import WebSocketDisconnect
        sid=self.create()
        with self.assertRaises(WebSocketDisconnect):
            with self.client.websocket_connect('/ws/live?session_id='+sid,headers={'Origin':'https://evil.example'}):pass
        self.client.cookies.clear()
        with self.assertRaises(WebSocketDisconnect):
            with self.client.websocket_connect('/ws/live?session_id='+sid,headers=self.headers):pass
    def test_reset_deletes_old_claim(self):
        old=self.create();s.append_turn(s.sessions[old],'Claimant','Old confidential claim')
        self.assertEqual(self.client.delete('/api/sessions/'+old,headers=self.headers).status_code,200)
        new=self.create();self.assertNotEqual(old,new)
        self.assertEqual(self.client.get('/api/sessions/'+old).status_code,404)
        self.assertEqual(len(self.client.get('/api/sessions/'+new).json()['state']['transcript']),1)
    def test_packet_download_contains_manifest_and_exact_image(self):
        sid=self.create();session=s.sessions[sid]
        session.evidence_photos.append(dict(id='photo1',frame_id='f1',data_url=s._data_url(b'JPEG','image/jpeg'),caption='Fixture',confirmed=False,claimant_description='',captured_at='2026-09-18',document_types=[]))
        response=self.client.get('/api/sessions/'+sid+'/packet')
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            self.assertEqual(archive.read('evidence/photo1.jpg'),b'JPEG')
            self.assertIn('evidence/photo1.jpg',archive.read('claim.md').decode())
            self.assertNotIn('data_url',json.loads(archive.read('evidence.json'))[0])
    def test_session_limit_and_source_not_served(self):
        for _ in range(4):self.create()
        self.assertEqual(self.client.post('/api/sessions',headers=self.headers).status_code,429)
        self.assertEqual(self.client.get('/server.py').status_code,404)


if __name__=='__main__':unittest.main(verbosity=2)
