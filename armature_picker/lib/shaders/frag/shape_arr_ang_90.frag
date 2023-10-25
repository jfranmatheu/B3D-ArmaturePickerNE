
// VERT_ID: ADVANCE_POINT_GRAPHIC

out vec4 fragColor;

uniform float u_size, u_line_width, u_antialias;
uniform vec4 u_stroke_color, u_bg_color;

uniform vec2 u_rotation;
// varying vec2 rotation;
// varying vec2 v_size;


// ----------------------------------------------------------------

void main()
{
    vec2 P = gl_PointCoord.xy - vec2(0.5, 0.5);
    P = vec2(u_rotation.x*P.x - u_rotation.y*P.y,
             u_rotation.y*P.x + u_rotation.x*P.y);
    // float d = marker(P*v_size, size);
    // u_body == u_size, u_head == u_body * 0.15
    float d = arrow_angle_90(P*u_size, u_size, u_size * 0.15, u_line_width, u_antialias);
    fragColor = outline(d, u_line_width, u_antialias, u_stroke_color, u_bg_color);
}
