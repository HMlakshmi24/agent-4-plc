"""
Enhanced Theme Integration System
Properly applies themes and positions AI-generated components in HTML templates
"""

import json
import re
from typing import Dict, List, Any

class EnhancedThemeIntegration:
    """Enhanced system for theme application and component positioning"""
    
    def __init__(self):
        self.themes = {
            'default': {
                'name': 'Industrial',
                'colors': {
                    'primary': '#00d4ff',
                    'secondary': '#0099cc',
                    'success': '#00ff88',
                    'warning': '#ffaa00',
                    'danger': '#ff3366',
                    'tank_fill': '#00d4ff',
                    'motor_color': '#00ff88',
                    'pipe_color': '#4a90d9'
                },
                'background': {
                    'primary': '#0a0e1a',
                    'secondary': '#151923',
                    'tertiary': '#1e2430'
                }
            },
            'water': {
                'name': 'Water System',
                'colors': {
                    'primary': '#0084C7',
                    'secondary': '#005A8B',
                    'success': '#00C896',
                    'warning': '#F39C12',
                    'danger': '#E74C3C',
                    'tank_fill': '#0084C7',
                    'motor_color': '#005A8B',
                    'pipe_color': '#0084C7'
                },
                'background': {
                    'primary': '#f0f8ff',
                    'secondary': '#ffffff',
                    'tertiary': '#e6f3ff'
                }
            },
            'motor': {
                'name': 'Motor Control',
                'colors': {
                    'primary': '#ff6b35',
                    'secondary': '#f7931e',
                    'success': '#00ff88',
                    'warning': '#ffaa00',
                    'danger': '#ff3366',
                    'tank_fill': '#ff6b35',
                    'motor_color': '#f7931e',
                    'pipe_color': '#ff6b35'
                },
                'background': {
                    'primary': '#1a1a1a',
                    'secondary': '#2d2d2d',
                    'tertiary': '#404040'
                }
            },
            'hvac': {
                'name': 'HVAC System',
                'colors': {
                    'primary': '#17a2b8',
                    'secondary': '#138496',
                    'success': '#28a745',
                    'warning': '#ffc107',
                    'danger': '#dc3545',
                    'tank_fill': '#17a2b8',
                    'motor_color': '#138496',
                    'pipe_color': '#17a2b8'
                },
                'background': {
                    'primary': '#f8f9fa',
                    'secondary': '#ffffff',
                    'tertiary': '#e9ecef'
                }
            }
        }
        
        self.component_positions = {
            'tank': {'default_x': 100, 'default_y': 150, 'spacing_x': 150},
            'pump': {'default_x': 250, 'default_y': 150, 'spacing_x': 150},
            'motor': {'default_x': 400, 'default_y': 150, 'spacing_x': 150},
            'valve': {'default_x': 550, 'default_y': 150, 'spacing_x': 100},
            'sensor_level': {'default_x': 100, 'default_y': 250, 'spacing_x': 150},
            'sensor_temp': {'default_x': 250, 'default_y': 250, 'spacing_x': 150},
            'sensor_pressure': {'default_x': 400, 'year': 250, 'spacing_x': 150},
            'gauge': {'default_x': 550, 'y': 250, 'spacing_x': 150},
            'button': {'default_x': 100, 'y': 350, 'spacing_x': 120},
            'alarm': {'default_x': 700, 'y': 150, 'spacing_x': 100}
        }
    
    def detect_theme_from_components(self, components: List[Dict]) -> str:
        """Detect appropriate theme based on component types"""
        component_types = [c.get('type', '').lower() for c in components]
        
        # HVAC system detection (highest priority for fan components)
        hvac_indicators = ['fan', 'hvac']
        if any(indicator in component_types for indicator in hvac_indicators):
            return 'hvac'
        
        # Water system detection
        water_indicators = ['tank', 'pump', 'sensor_level', 'valve']
        if any(indicator in component_types for indicator in water_indicators):
            water_score = sum(1 for t in component_types if t in water_indicators)
            if water_score >= 2:
                return 'water'
        
        # Motor system detection
        motor_indicators = ['motor']
        if any(indicator in component_types for indicator in motor_indicators):
            return 'motor'
        
        return 'default'
    
    def position_components(self, components: List[Dict]) -> List[Dict]:
        """Intelligently position components in a grid layout"""
        positioned_components = []
        
        # Position each component
        for i, component in enumerate(components):
            comp_type = component.get('type', '').lower()
            
            if comp_type in self.component_positions:
                pos_config = self.component_positions[comp_type]
                base_x = pos_config.get('default_x', 100)
                base_y = pos_config.get('default_y', 150)
                spacing_x = pos_config.get('spacing_x', 150)
                
                # Calculate position based on component index and type
                if comp_type == 'tank':
                    # Tanks arranged horizontally
                    x = base_x + i * spacing_x
                    y = base_y
                elif comp_type == 'pump':
                    # Pumps below tanks
                    x = base_x + i * spacing_x
                    y = base_y + 100
                elif comp_type == 'motor':
                    # Motors arranged in a row
                    x = base_x + i * spacing_x
                    y = base_y
                elif comp_type in ['sensor_level', 'sensor_temp', 'sensor_pressure']:
                    # Sensors below main components
                    x = base_x + i * spacing_x
                    y = base_y + 100
                elif comp_type == 'valve':
                    # Valves between components
                    x = base_x + i * spacing_x
                    y = base_y
                elif comp_type == 'gauge':
                    # Gauges on the right
                    x = base_x + i * spacing_x
                    y = base_y
                elif comp_type == 'button':
                    # Buttons at the bottom
                    x = base_x + i * spacing_x
                    y = base_y
                else:
                    # Default positioning
                    x = base_x
                    y = base_y
                
                component['x'] = x
                component['y'] = y
            else:
                # Default positioning
                component['x'] = 100
                component['y'] = 150
            
            positioned_components.append(component)
        
        return positioned_components
    
    def generate_pipes(self, components: List[Dict]) -> List[Dict]:
        """Generate pipes between components based on logical flow"""
        pipes = []
        pipe_id = 1
        
        # Group components by type
        tanks = [c for c in components if c.get('type') == 'tank']
        pumps = [c for c in components if c.get('type') == 'pump']
        valves = [c for c in components if c.get('type') == 'valve']
        
        # Connect tanks to pumps
        for tank in tanks:
            for pump in pumps:
                if abs(tank['x'] - pump['x']) < 200:  # Close enough
                    pipes.append({
                        'id': f'pipe_{pipe_id}',
                        'x1': tank['x'] + 40,  # Right edge of tank
                        'y1': tank['y'],
                        'x2': pump['x'] - 25,  # Left edge of pump
                        'y2': pump['y']
                    })
                    pipe_id += 1
        
        # Connect pumps to valves
        for pump in pumps:
            for valve in valves:
                if abs(pump['x'] - valve['x']) < 200:
                    pipes.append({
                        'id': f'pipe_{pipe_id}',
                        'x1': pump['x'] + 25,  # Right edge of pump
                        'y1': pump['y'],
                        'x2': valve['x'],  # Center of valve
                        'y2': valve['y']
                    })
                    pipe_id += 1
        
        return pipes
    
    def enhance_layout(self, layout: Dict) -> Dict:
        """Enhance layout with proper theme and positioning"""
        enhanced_layout = layout.copy()
        
        # Detect and apply theme
        components = layout.get('components', [])
        detected_theme = self.detect_theme_from_components(components)
        enhanced_layout['theme'] = detected_theme
        
        # Position components
        positioned_components = self.position_components(components)
        enhanced_layout['components'] = positioned_components
        
        # Generate pipes for P&ID
        if 'pid' in layout.get('system_name', '').lower():
            pipes = self.generate_pipes(positioned_components)
            enhanced_layout['pipes'] = pipes
        
        # Add theme metadata
        enhanced_layout['theme_info'] = {
            'detected_theme': detected_theme,
            'theme_name': self.themes[detected_theme]['name'],
            'colors': self.themes[detected_theme]['colors'],
            'background': self.themes[detected_theme]['background']
        }
        
        return enhanced_layout
    
    def generate_enhanced_hmi_html(self, layout: Dict) -> str:
        """Generate enhanced HMI HTML with proper theme application"""
        enhanced_layout = self.enhance_layout(layout)
        
        # Load the enhanced template
        template_path = "ENHANCED_INDUSTRIAL_HMI_TEMPLATE.html"
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
        except FileNotFoundError:
            # Fallback to basic HTML generation
            return self.generate_basic_hmi_html(enhanced_layout)
        
        # Apply theme to body
        theme = enhanced_layout.get('theme', 'default')
        template = template.replace('data-theme="default"', f'data-theme="{theme}"')
        
        # Update theme indicator
        theme_name = self.themes[theme]['name']
        template = template.replace('Default Theme', theme_name)
        
        # Generate JavaScript for component loading
        component_js = self.generate_component_js(enhanced_layout)
        
        # Replace the placeholder loadComponents function
        template = re.sub(
            r'loadComponents\(\) \{.*?\n        \}',
            component_js,
            template,
            flags=re.DOTALL
        )
        
        return template
    
    def generate_enhanced_pid_html(self, layout: Dict) -> str:
        """Generate enhanced P&ID HTML with proper theme and positioning"""
        enhanced_layout = self.enhance_layout(layout)
        
        # Load the enhanced template
        template_path = "ENHANCED_INDUSTRIAL_PID_TEMPLATE.html"
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
        except FileNotFoundError:
            # Fallback to basic HTML generation
            return self.generate_basic_pid_html(enhanced_layout)
        
        # Apply theme to body
        theme = enhanced_layout.get('theme', 'default')
        template = template.replace('data-theme="default"', f'data-theme="{theme}"')
        
        # Update theme indicator
        theme_name = self.themes[theme]['name']
        template = template.replace('Industrial', theme_name)
        
        # Generate JavaScript for layout loading
        layout_js = self.generate_layout_js(enhanced_layout)
        
        # Replace the placeholder loadSampleLayout function
        template = re.sub(
            r'loadSampleLayout\(\) \{.*?\n            \}',
            layout_js,
            template,
            flags=re.DOTALL
        )
        
        return template
    
    def generate_component_js(self, layout: Dict) -> str:
        """Generate JavaScript for loading components"""
        components = layout.get('components', [])
        
        js_components = []
        for comp in components:
            comp_data = {
                'id': comp.get('id', f"comp_{len(js_components)}"),
                'type': comp.get('type', 'unknown'),
                'name': comp.get('name', comp.get('type', 'Unknown')),
                'value': comp.get('value', 50),
                'status': comp.get('status', 'stopped')
            }
            js_components.append(comp_data)
        
        return f'''
        loadComponents() {{
            const enhancedComponents = {json.dumps(js_components, indent=12)};
            
            enhancedComponents.forEach(component => {{
                this.componentManager.addComponent(component);
            }});

            this.updateComponentList();
            
            // Apply theme
            this.componentManager.themeManager.setTheme('{layout.get('theme', 'default')}');
        }}'''
    
    def generate_layout_js(self, layout: Dict) -> str:
        """Generate JavaScript for loading P&ID layout"""
        components = layout.get('components', [])
        pipes = layout.get('pipes', [])
        
        js_components = []
        for comp in components:
            comp_data = {
                'id': comp.get('id', f"comp_{len(js_components)}"),
                'type': comp.get('type', 'unknown'),
                'name': comp.get('name', comp.get('type', 'Unknown')),
                'x': comp.get('x', 100),
                'y': comp.get('y', 150),
                'value': comp.get('value', 50),
                'tag': comp.get('tag', f"{comp.get('type', 'UNK').upper()}-{len(js_components)+101:03d}")
            }
            js_components.append(comp_data)
        
        return f'''
        loadSampleLayout() {{
            // Enhanced layout with theme: {layout.get('theme', 'default')}
            const enhancedComponents = {json.dumps(js_components, indent=12)};
            const enhancedPipes = {json.dumps(pipes, indent=12)};

            enhancedComponents.forEach(component => {{
                this.addComponent(component);
            }});
            
            enhancedPipes.forEach(pipe => {{
                this.addPipe(pipe);
            }});
            
            // Apply detected theme
            this.setTheme('{layout.get('theme', 'default')}');
        }}'''
    
    def generate_basic_hmi_html(self, layout: Dict) -> str:
        """Fallback basic HMI HTML generation"""
        theme = layout.get('theme', 'default')
        colors = self.themes[theme]['colors']
        bg = self.themes[theme]['background']
        
        components = layout.get('components', [])
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{layout.get('system_name', 'HMI System')}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background: {bg['primary']};
            color: white;
            margin: 0;
            padding: 20px;
        }}
        .component {{
            background: {bg['secondary']};
            border: 2px solid {colors['primary']};
            border-radius: 8px;
            padding: 15px;
            margin: 10px;
            display: inline-block;
        }}
        .tank {{
            width: 100px;
            height: 150px;
            background: {colors['tank_fill']};
            border-radius: 0 0 10px 10px;
            position: relative;
        }}
        .motor {{
            width: 80px;
            height: 80px;
            background: {colors['motor_color']};
            border-radius: 50%;
        }}
    </style>
</head>
<body>
    <h1>{layout.get('system_name', 'HMI System')}</h1>
    <div class="theme-info">Theme: {self.themes[theme]['name']}</div>
    
    <div class="components">'''
        
        for comp in components:
            comp_type = comp.get('type', 'unknown')
            comp_name = comp.get('name', comp_type.title())
            
            html += f'''
        <div class="component">
            <h3>{comp_name}</h3>
            <div class="{comp_type}"></div>
            <p>Type: {comp_type}</p>
        </div>'''
        
        html += '''
    </div>
</body>
</html>'''
        
        return html
    
    def generate_basic_pid_html(self, layout: Dict) -> str:
        """Fallback basic P&ID HTML generation"""
        theme = layout.get('theme', 'default')
        colors = self.themes[theme]['colors']
        bg = self.themes[theme]['background']
        
        components = layout.get('components', [])
        pipes = layout.get('pipes', [])
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{layout.get('system_name', 'P&ID System')}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background: {bg['primary']};
            color: white;
            margin: 0;
            padding: 20px;
        }}
        .pid-container {{
            background: {bg['secondary']};
            border: 2px solid {colors['primary']};
            border-radius: 8px;
            padding: 20px;
        }}
        .component {{
            position: absolute;
            background: {bg['tertiary']};
            border: 2px solid {colors['primary']};
            border-radius: 4px;
            padding: 5px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <h1>{layout.get('system_name', 'P&ID System')}</h1>
    <div class="theme-info">Theme: {self.themes[theme]['name']}</div>
    
    <div class="pid-container" style="position: relative; height: 400px;">'''
        
        # Add components with positioning
        for comp in components:
            comp_type = comp.get('type', 'unknown')
            comp_name = comp.get('name', comp_type.title())
            x = comp.get('x', 100)
            y = comp.get('y', 150)
            
            html += f'''
        <div class="component" style="left: {x}px; top: {y}px;">
            <div>{comp_name}</div>
            <small>{comp_type}</small>
        </div>'''
        
        html += '''
    </div>
</body>
</html>'''
        
        return html

# Global instance
enhanced_theme_integration = EnhancedThemeIntegration()

def apply_enhanced_theme_and_positioning(layout: Dict, output_type: str = 'hmi') -> str:
    """
    Apply enhanced theme and positioning to layout
    
    Args:
        layout: AI-generated layout dictionary
        output_type: 'hmi' or 'pid'
    
    Returns:
        Enhanced HTML string
    """
    if output_type.lower() == 'hmi':
        return enhanced_theme_integration.generate_enhanced_hmi_html(layout)
    elif output_type.lower() == 'pid':
        return enhanced_theme_integration.generate_enhanced_pid_html(layout)
    else:
        raise ValueError(f"Unknown output type: {output_type}")

def detect_and_apply_theme(components: List[Dict]) -> Dict:
    """
    Detect theme and apply to components
    
    Args:
        components: List of component dictionaries
    
    Returns:
        Enhanced layout dictionary
    """
    layout = {
        'components': components,
        'system_name': 'Enhanced System'
    }
    
    return enhanced_theme_integration.enhance_layout(layout)
