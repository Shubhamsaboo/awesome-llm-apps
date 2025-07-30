"""
Local Streamlit-Float Implementation
streamlit-float 핵심 기능 로컬 구현 - Float Helper만 포함
"""

import streamlit as st
import streamlit.components.v1 as components
import uuid


def float_init():
    """Float 기능 초기화 - CSS 및 JavaScript 주입"""
    
    html_style = '''
    <style>
    div.element-container:has(div.float) {
        position: absolute!important;
    }
    div.element-container:has(div.floating) {
        position: absolute!important;
    }
    div:has( >.element-container div.float) {
        display: flex;
        flex-direction: column;
        position: fixed;
        z-index: 99;
    }
    div.float, div.elim {
        display: none;
        height:0%;
    }
    div.floating {
        display: flex;
        flex-direction: column;
        position: fixed;
        z-index: 99; 
    }
    </style>
    '''
    st.markdown(html_style, unsafe_allow_html=True)


def float_css_helper(width=None, height=None, top=None, left=None, right=None, bottom=None, 
                    background=None, border=None, z_index=None, border_radius=None,
                    box_shadow=None, backdrop_filter=None, transform=None, css="", **kwargs):
    """CSS 스타일 문자열 생성 헬퍼"""
    
    jct_css = ""
    
    if width is not None:
        jct_css += f"width: {width};"
    if height is not None:
        jct_css += f"height: {height};"
    if top is not None:
        jct_css += f"top: {top};"
    if left is not None:
        jct_css += f"left: {left};"
    if right is not None:
        jct_css += f"right: {right};"
    if bottom is not None:
        jct_css += f"bottom: {bottom};"
    if background is not None:
        jct_css += f"background: {background};"
    if border is not None:
        jct_css += f"border: {border};"
    if z_index is not None:
        jct_css += f"z-index: {z_index};"
    if border_radius is not None:
        jct_css += f"border-radius: {border_radius};"
    if box_shadow is not None:
        jct_css += f"box-shadow: {box_shadow};"
    if backdrop_filter is not None:
        jct_css += f"backdrop-filter: {backdrop_filter};"
    if transform is not None:
        jct_css += f"transform: {transform};"
    
    if isinstance(css, str):
        jct_css += css
    
    for key, value in kwargs.items():
        css_key = key.replace('_', '-')
        jct_css += f"{css_key}: {value};"
    
    return jct_css


def sf_float(self, css=None):
    """컨테이너에 float 기능 추가하는 메서드"""
    
    if css is not None:
        new_id = str(uuid.uuid4())[:8]
        
        # 기본 float CSS
        new_css = f'''
        <style>
        div.element-container[data-testid="element-container"]:has(>div div.flt-{new_id}) {{
            position: absolute!important;
        }}
        div:has( >.element-container div.flt-{new_id}) {{
            {css}
        }}
        </style>
        '''
        
        self.markdown(new_css + f'\n<div class="float flt-{new_id}"></div>', unsafe_allow_html=True)
        
        # 기본 JavaScript
        js_code = f'''
        <script>
        (function() {{
            const float_el = parent.document.querySelectorAll('div[class="float flt-{new_id}"]');
            if (float_el.length > 0) {{
                const float_el_parent = float_el[0].closest("div > .element-container").parentNode;
                float_el_parent.id = "float-this-component-{new_id}";
                float_el_parent.style.cssText = 'display:flex; flex-direction:column; position:fixed; z-index:99; {css}';
                
                // 기본 이프레임 숨김
                const iframes = parent.document.querySelectorAll('iframe[srcdoc*="{new_id}"]');
                iframes.forEach(iframe => {{
                    if (iframe.parentNode) {{
                        iframe.parentNode.style.display = 'none';
                    }}
                }});
                
                // Float 요소 자체 숨김
                const float_el_hide = parent.document.querySelectorAll('div[class="float flt-{new_id}"]')[0].closest("div > .element-container");
                if (float_el_hide) {{
                    float_el_hide.style.display = 'none';
                }}
            }}
        }})();
        </script>
        '''
        
        components.html(js_code, height=0, width=0)
        
        return f'div:has( >.element-container div.flt-{new_id})'
    else:
        self.markdown('<div class="float"></div>', unsafe_allow_html=True)
        return 'div:has( >.element-container div.float)'


# Streamlit 컨테이너에 float 메서드 추가
if not hasattr(st.delta_generator.DeltaGenerator, 'float'):
    st.delta_generator.DeltaGenerator.float = sf_float
