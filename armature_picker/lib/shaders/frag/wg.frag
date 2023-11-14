// @vert_id: WG

#pragma BLENDER_REQUIRE(gpu_shader_colorspace_lib.glsl)

in vec2 uv;

uniform vec2 u_dimensions;
uniform vec4 u_color;
//uniform vec4 u_outline_color;
uniform float u_outline_color_factor;
uniform float u_radius;
uniform float u_outline;

out vec4 fragColor;

#define cir_top_left (vec2(0, u_dimensions.y) + vec2(u_radius, -u_radius))
#define cir_top_right (vec2(u_dimensions.x, u_dimensions.y) + vec2(-u_radius, -u_radius))
#define cir_bot_left vec2(u_radius)
#define cir_bot_right (vec2(u_dimensions.x, 0) + vec2(-u_radius, u_radius))


void main(void){
    vec2 coords = uv * u_dimensions;

    float radius = u_radius-.5f;
    float amp_radius = u_radius+.5f;
    float len = 0.0;

    if (coords.x < cir_top_left.x && coords.y > cir_top_left.y)// && length(coords - cir_top_left) > radius)
    {
        len = length(coords - cir_top_left);
    }
    else if (coords.x > cir_top_right.x && coords.y > cir_top_right.y)// && length(coords - cir_top_right) > radius)
    {
        len = length(coords - cir_top_right);
    }
    else if (coords.x < cir_bot_left.x && coords.y < cir_bot_left.y)// && length(coords - cir_bot_left) > radius)
    {
        len = length(coords - cir_bot_left);
    }
    else if (coords.x > cir_bot_right.x && coords.y < cir_bot_right.y)// && length(coords - cir_bot_right) > radius)
    {
        len = length(coords - cir_bot_right);
    }

    if (len > amp_radius)
        discard;

    float alpha = smoothstep(amp_radius, radius, len);


    fragColor = u_color;
    if (u_outline != 0 && u_radius != 0) {
        float outline_factor = smoothstep(0.0, 1.0, uv.x) + smoothstep(1.0, 0.0, uv.y);
        if (len >= u_radius-u_outline) {
            //if (len >= u_radius-u_outline-0.5) {
            //    fragColor =  mix(fragColor, pow(fragColor, vec4(.8+.3*outline_factor)), smoothstep(u_radius-u_outline-1, u_radius-u_outline-0.5, len));
            //}
            //else
            fragColor = pow(fragColor, vec4(u_outline_color_factor+.3*outline_factor)); // mix(fragColor, u_outline_color, outline_factor); // pow(fragColor, vec4(.8+.3*outline_factor));
        }
        else if ( (coords.x <= u_outline) || (coords.y <= u_outline) || (coords.x >= u_dimensions.x-u_outline) || (coords.y >= u_dimensions.y-u_outline) ) {
            fragColor = pow(fragColor, vec4(u_outline_color_factor+.3*outline_factor)); // mix(fragColor, u_outline_color, outline_factor); // pow(fragColor, vec4(.8+.3*outline_factor));
        }
    }
    fragColor.a *= alpha;
    // fragColor = blender_srgb_to_framebuffer_space(fragColor);
}