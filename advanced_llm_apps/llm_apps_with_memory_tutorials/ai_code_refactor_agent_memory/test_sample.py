#!/usr/bin/env python3
"""
Quick test of the AI Code Refactor Agent with sample code
"""

from refactor_agent import CodeRefactorAgent
from memory_schema import OutcomeStatus

def main():
    # Initialize agent with Ollama on port 11435
    print("[*] Initializing AI Code Refactor Agent...")
    agent = CodeRefactorAgent(
        model="mistral",
        ollama_host="http://localhost:11435"
    )
    print(f"[OK] Agent initialized with model: {agent.model}")
    print(f"     Ollama host: {agent.ollama_host}\n")
    
    # Sample 1: Procedural code to refactor
    sample_code_1 = '''def process_users(users, min_age=18, filter_active=True):
    """Process user data"""
    result = []
    for user in users:
        if user['age'] >= min_age:
            if filter_active and user['active']:
                result.append({
                    'id': user['id'],
                    'name': user['name'],
                    'email': user['email']
                })
            elif not filter_active:
                result.append({
                    'id': user['id'],
                    'name': user['name'],
                    'email': user['email']
                })
    return result'''
    
    print("=" * 70)
    print("TEST 1: Refactor procedural code to add type hints")
    print("=" * 70)
    print("\n📝 Original code:")
    print(sample_code_1)
    print("\n🔄 Running refactor task: add_type_hints...")
    
    outcome_1 = agent.refactor_code(
        code=sample_code_1,
        task="Add proper type hints and improve the function signature",
        refactoring_type="add_type_hints"
    )
    
    print(f"\n✓ Status: {outcome_1.status}")
    print(f"  Attempt: {outcome_1.attempt_number}")
    if outcome_1.status == OutcomeStatus.SUCCESS.value or outcome_1.status == "SUCCESS":
        print(f"\n✨ Refactored code (first 500 chars):")
        print(outcome_1.code_output[:500] if outcome_1.code_output else "N/A")
        print(f"\n💡 Key insight: {outcome_1.key_insight[:200] if outcome_1.key_insight else 'N/A'}")
    else:
        print(f"\n❌ Error: {outcome_1.error_message}")
    
    # Sample 2: Simple code to simplify
    sample_code_2 = '''def check_admin(user):
    if user is not None:
        if user.get('role') is not None:
            if user.get('role') == 'admin':
                if user.get('active') is not None:
                    if user.get('active') == True:
                        return True
    return False'''
    
    print("\n" + "=" * 70)
    print("TEST 2: Simplify complex nested logic")
    print("=" * 70)
    print("\n📝 Original code:")
    print(sample_code_2)
    print("\n🔄 Running refactor task: simplify_logic...")
    
    outcome_2 = agent.refactor_code(
        code=sample_code_2,
        task="Simplify nested conditions and make more Pythonic",
        refactoring_type="simplify_logic"
    )
    
    print(f"\n✓ Status: {outcome_2.status}")
    print(f"  Attempt: {outcome_2.attempt_number}")
    if outcome_2.status == OutcomeStatus.SUCCESS.value or outcome_2.status == "SUCCESS":
        print(f"\n✨ Refactored code (first 500 chars):")
        print(outcome_2.code_output[:500] if outcome_2.code_output else "N/A")
        print(f"\n💡 Key insight: {outcome_2.key_insight[:200] if outcome_2.key_insight else 'N/A'}")
    else:
        print(f"\n❌ Error: {outcome_2.error_message}")
    
    # Print session summary
    print("\n" + "=" * 70)
    print("SESSION SUMMARY")
    print("=" * 70)
    summary = agent.get_session_summary()
    print(f"📊 Total refactorings: {summary['total_refactorings']}")
    print(f"✅ Successful: {summary['successful']}")
    print(f"❌ Failed: {summary['failed']}")
    success_rate = summary['success_rate']
    if isinstance(success_rate, str):
        success_rate = float(success_rate.rstrip('%')) / 100
    print(f"📈 Success rate: {success_rate:.1%}")
    print(f"🧠 Constraints discovered: {summary['constraints_discovered']}")
    print(f"🔄 Strategy adaptations: {summary['adaptations']}")
    
    if agent.discovered_constraints:
        print(f"\n📝 Learned constraints:")
        for constraint in agent.discovered_constraints[:3]:
            print(f"   - {constraint.constraint[:80]}... (Severity: {constraint.severity})")
    
    print("\n✅ Test completed successfully!")

if __name__ == "__main__":
    main()
