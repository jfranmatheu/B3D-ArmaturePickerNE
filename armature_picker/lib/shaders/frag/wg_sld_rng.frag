// @vert_id: UV

#pragma BLENDER_REQUIRE(gpu_shader_colorspace_lib.glsl)

#define PI 3.14159265358979323846

in vec2 uv;

// uniform vec2 u_dimensions;
uniform float u_arc_angle;
uniform float u_angle;
uniform float u_thickness;
uniform vec4 u_color;
uniform vec4 u_fill_color;
uniform float u_invert_angle;

out vec4 fragColor;

#define RAD_MIN u_thickness
#define RAD_MAX 0.98f
#define RAD_MID (RAD_MAX - RAD_MIN) / 2.0f
#define RAD_DIF 0.03f

#define ANG_MIN u_angle-0.02f
#define ANG_MAX u_angle+0.02f
#define ANG_DIF 0.02f

// #define CXY 0.5 * u_dimensions


void main(void){
    // vec2 coords = uv * u_dimensions;

    vec2 cxy = 2.0 * uv - 1.0;
    float r = dot(cxy, cxy);
    float delta = fwidth(r);
    float alpha = 1.0 - smoothstep(1.0 - delta, 1.0 + delta, r);
    if (alpha < 0.05) // threshold
        discard;

    // Use polar coordinates instead of cartesian
    vec2 toCenter = vec2(0.5)-uv.xy;
    float angle = atan(toCenter.y, toCenter.x);

    if (cxy.y < 1.0)
        angle = PI - angle;
    
    if (u_invert_angle == 1.0) {
        angle = (PI * 2) - angle;
    }

    if (angle > u_arc_angle)
        discard;

    float radius = length(toCenter)*2.0;

    if (radius < RAD_MIN || radius > RAD_MAX)
        discard;
    if (radius >= RAD_MIN && radius < RAD_MIN + RAD_DIF)
        alpha = smoothstep(RAD_MIN, RAD_MIN + RAD_DIF, radius);
    else if (radius >= RAD_MAX - RAD_DIF && radius < RAD_MAX)
        alpha = smoothstep(RAD_MAX, RAD_MAX - RAD_DIF, radius);

    float mix_factor = .5;

    if (angle<ANG_DIF || angle>2*PI-ANG_DIF)
        fragColor = vec4(.4);
    else if (abs(angle-u_angle) < ANG_DIF) {

        if (angle > ANG_MIN && angle < ANG_MAX)
            mix_factor = smoothstep(ANG_MIN, ANG_MAX, angle);
        fragColor = mix(u_fill_color, pow(u_fill_color, vec4(1.1)), angle);
        fragColor = mix(fragColor, u_color, mix_factor);
    }
    else {
        if (angle > u_angle){
            //if (radius > RAD_MAX-RAD_DIF*1.5)
            //    fragColor = pow(u_color, vec4(1.1));
            if (radius <= RAD_MID)
                mix_factor = smoothstep(RAD_MID, RAD_MIN*.95, radius);
            else
                mix_factor = smoothstep(RAD_MID, RAD_MAX, radius);
            fragColor = mix(u_color, pow(u_color, vec4(1.2)), mix_factor);
        }
        else
            fragColor = mix(u_fill_color, pow(u_fill_color, vec4(1.1)), angle);
    }

    fragColor.a *= alpha;
    // fragColor = blender_srgb_to_framebuffer_space(fragColor);
}