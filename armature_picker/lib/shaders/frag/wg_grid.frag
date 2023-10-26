// @vert_id: WG

#pragma BLENDER_REQUIRE(gpu_shader_colorspace_lib.glsl)

in vec2 uv;

uniform vec2 u_dimensions;
uniform vec4 u_color;
//uniform vec4 u_outline_color;
uniform float u_outline_color_factor;
uniform float u_radius;
uniform float u_outline;
uniform vec4 u_grid_color;
uniform vec2 u_offset;
uniform float u_scale; // Grid transformation.

out vec4 fragColor;

#define cir_top_left (vec2(0, u_dimensions.y) + vec2(u_radius, -u_radius))
#define cir_top_right (vec2(u_dimensions.x, u_dimensions.y) + vec2(-u_radius, -u_radius))
#define cir_bot_left vec2(u_radius)
#define cir_bot_right (vec2(u_dimensions.x, 0) + vec2(-u_radius, u_radius))


float random(in float x){ return fract(sin(x)*43758.5453); }
float random(in vec2 st){ return fract(sin(dot(st.xy ,vec2(12.9898,78.233))) * 43758.5453); }

float grid(vec2 st, float res){
    vec2 grid = fract(st*res);
    return 1.-(step(res,grid.x) * step(res,grid.y));
}

float box(in vec2 st, in vec2 size){
    size = vec2(0.5) - size*0.5;
    vec2 uv = smoothstep(size,
                        size+vec2(0.001),
                        st);
    uv *= smoothstep(size,
                    size+vec2(0.001),
                    vec2(1.0)-st);
    return uv.x*uv.y;
}

float cross(in vec2 st, vec2 size){
    return  clamp(box(st, vec2(size.x*0.5,size.y*0.125)) +
            box(st, vec2(size.y*0.125,size.x*0.5)),0.,1.);
}

float nice_grid(vec2 st, float res)
{
  vec2 grid = fract(st * res);
  return (step(res, grid.x) * step(res, grid.y));
}

vec2 transform_translate(vec2 position, vec2 offset)
{
    //move samplepoint in the opposite direction that we want to move shapes in
    return position - offset;
}

vec2 transform_scale(vec2 position, float scale)
{
    return position / scale;
}


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

    vec2 st = uv.xy * 2 - 1; // + 0.5/2.5; // gl_FragCoord.st/u_dimensions.xy;
    st.x *= u_dimensions.x/u_dimensions.y;

    st = transform_translate(st, u_offset);
    st = transform_scale(st, u_scale);

    vec3 color = u_color.rgb;

    // Grid
    vec2 grid_st = st*25.;
    color += vec3(0.4)*grid(grid_st, 0.01);
    color += vec3(0.2)*grid(grid_st, 0.02);
    color += vec3(0.2)*grid(grid_st, 0.1);

    // Crosses
    // vec2 crosses_st = st + .5;
    // crosses_st *= 3.;
    // vec2 crosses_st_f = fract(crosses_st);
    // color *= 1.-cross(crosses_st_f,vec2(.3,.3));
    // color += vec3(.9)*cross(crosses_st_f,vec2(.2,.2));

    fragColor = vec4(color, u_color.a);

    //float scale = u_dimensions.x * .5;
    //float resolution = .2;
    //vec2 grid_uv = uv.xy * scale; // scale
    //float x = grid(grid_uv, resolution); // resolution
    //fragColor = mix(u_color, vec4(pow(u_color.rgb, vec3(1.2)), u_color.a), x);

    if (u_outline != 0 && u_radius != 0) {
        float outline_factor = smoothstep(0.0, 1.0, uv.x) + smoothstep(1.0, 0.0, uv.y);
        if (len >= u_radius-u_outline) {
            //if (len >= u_radius-u_outline-0.5) {
            //    fragColor =  mix(fragColor, pow(fragColor, vec4(.8+.3*outline_factor)), smoothstep(u_radius-u_outline-1, u_radius-u_outline-0.5, len));
            //}
            //else
            fragColor = pow(u_color, vec4(u_outline_color_factor+.3*outline_factor)); // mix(fragColor, u_outline_color, outline_factor); // pow(fragColor, vec4(.8+.3*outline_factor));
        }
        else if ( (coords.x <= u_outline) || (coords.y <= u_outline) || (coords.x >= u_dimensions.x-u_outline) || (coords.y >= u_dimensions.y-u_outline) ) {
            fragColor = pow(u_color, vec4(u_outline_color_factor+.3*outline_factor)); // mix(fragColor, u_outline_color, outline_factor); // pow(fragColor, vec4(.8+.3*outline_factor));
        }
    }
    fragColor.a *= alpha;
    fragColor = blender_srgb_to_framebuffer_space(fragColor);
}