// @vert_id: BASIC_UV

#pragma BLENDER_REQUIRE(gpu_shader_colorspace_lib.glsl)

#ifdef GL_ES
precision mediump float;
#endif

in vec2 uv;

uniform vec2 u_dimensions;
uniform float u_factor;
uniform vec4 u_color;
uniform vec4 u_fill_color;
uniform float u_radius;

out vec4 fragColor;

#define cir_top_left (vec2(0, u_dimensions.y) + vec2(u_radius, -u_radius))
#define cir_top_right (vec2(u_dimensions.x, u_dimensions.y) + vec2(-u_radius, -u_radius))
#define cir_bot_left vec2(u_radius)
#define cir_bot_right (vec2(u_dimensions.x, 0) + vec2(-u_radius, u_radius))
#define cir_slide vec2(u_dimensions.x*u_factor-u_dimensions.y/2.0, u_dimensions.y/2.0)

#define fill_width u_factor * u_dimensions.x

void main(void){
    vec2 coords = uv * u_dimensions;

    float radius = u_radius-.5f;
    float amp_radius = u_radius+.5f;
    float len = 0.0;

    if (coords.x < cir_top_left.x && coords.y > cir_top_left.y && length(coords - cir_top_left) > radius)
    {
        len = length(coords - cir_top_left);
    }
    else if (coords.x > cir_top_right.x && coords.y > cir_top_right.y && length(coords - cir_top_right) > radius)
    {
        len = length(coords - cir_top_right);
    }
    else if (coords.x < cir_bot_left.x && coords.y < cir_bot_left.y && length(coords - cir_bot_left) > radius)
    {
        len = length(coords - cir_bot_left);
    }
    else if (coords.x > cir_bot_right.x && coords.y < cir_bot_right.y && length(coords - cir_bot_right) > radius)
    {
        len = length(coords - cir_bot_right);
    }
    
    if (len > amp_radius)
        discard;

    
    float alpha = smoothstep(amp_radius, radius, len);


    /*
    if ( (len > radius-1.0) || (coords.x < 1.0f) || (coords.x > (u_dimensions.x-1.0f)) || (coords.y < 1.0f) || (coords.y > (u_dimensions.y-1.0f)) ) {
        fragColor = pow(u_color, vec4(.9));
    }
    else {
        if (uv.x > u_factor)
            fragColor = u_color;
        else {
            if ( (coords.x > cir_slide.x) && (length(coords - cir_slide) > u_radius*2.0) )
                fragColor = u_color;
            else
                fragColor = u_fill_color;
        }
            
        fragColor.rgb = pow(fragColor.rgb, vec3(mix(1.0, 1.2, uv.x)));
    }
    */

    if (u_factor >= uv.x) {
        if ( (coords.x > (cir_slide.x + cir_slide.y)) ) // && (length(coords - cir_slide) > radius) )
            fragColor = u_color;
        else if (coords.x < cir_slide.x)
            fragColor = u_fill_color;
        else {
            radius = cir_slide.y * 1.3;
            len = length(coords - cir_slide);
            //radius = u_dimensions.y/2.0;
            amp_radius = radius + 0.5;
            radius -= 0.5;

            float mix_factor = smoothstep(amp_radius, radius, len);
            fragColor = mix(u_color, u_fill_color, mix_factor);
        }
    }
    else
        fragColor = u_color;

    fragColor.a *= alpha;
    // fragColor = blender_srgb_to_framebuffer_space(fragColor);
}
