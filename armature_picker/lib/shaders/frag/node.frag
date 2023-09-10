in vec2 uv;
out vec4 fragColor;

uniform vec2 u_dimensions;
uniform vec4 u_main_color;
// uniform float u_opacity;
uniform float u_radius;
uniform float u_line_thickness;
uniform float u_header_height;
uniform float u_outline_thickness;

const float u_opacity = u_main_color.a;
const vec3 body_color = u_main_color.rgb; // vec3(0.008); // vec3(.11); //
const vec3 u_outline_color = pow(body_color, vec3(1.2));
const vec3 u_line_color = pow(body_color, vec3(1.2)); // vec3(.64)); // vec3(0.05);
const vec3 header_color = pow(body_color, vec3(0.75)); // vec3(0.016); //  vec3(.08); //
const vec3 header_color_gradient = pow(body_color, vec3(0.85)); // vec3(0.01);

#  define cir_top_left vec2(u_radius + u_outline_thickness, u_dimensions.y - (u_radius + u_outline_thickness))
#  define cir_top_right vec2(u_dimensions.x - (u_radius + u_outline_thickness),  u_dimensions.y - (u_radius + u_outline_thickness))
#  define cir_bot_left vec2(u_radius + u_outline_thickness)
#  define cir_bot_right vec2(u_dimensions.x - (u_radius + u_outline_thickness), u_radius + u_outline_thickness)

void main()
{
  vec2 coords = uv * u_dimensions;

  vec3 color = body_color; // vec3(uv.xy, 0.0); // position map

  float radius = u_radius;
  float rad_with_outline = radius + u_outline_thickness;
  float alpha = 1.0;
  float len = 0.0;

  if (coords.x < cir_top_left.x && coords.y > cir_top_left.y) // && length(coords - cir_top_left) > rad_with_outline)
  {
    len = length(coords - cir_top_left);
  }
  else if (coords.x > cir_top_right.x && coords.y > cir_top_right.y) // && length(coords - cir_top_right) > rad_with_outline)
  {
    len = length(coords - cir_top_right);
  }
  else if (coords.x < cir_bot_left.x && coords.y < cir_bot_left.y) // && length(coords - cir_bot_left) > rad_with_outline)
  {
    len = length(coords - cir_bot_left);
  }
  else if (coords.x > cir_bot_right.x && coords.y < cir_bot_right.y) // && length(coords - cir_bot_right) > rad_with_outline)
  {
    len = length(coords - cir_bot_right);
  }

  if (len < rad_with_outline+1.0 && len > radius)
    alpha = 1.0;
  else if (len > radius)
    discard;

  alpha = smoothstep(rad_with_outline+1.0, rad_with_outline-0.65, len);

  if (u_outline_thickness!=0 && ( (len < rad_with_outline && len > radius) || coords.x <= u_outline_thickness || coords.x >= (u_dimensions.x - u_outline_thickness) || coords.y <= u_outline_thickness || coords.y >= (u_dimensions.y - u_outline_thickness))) {
    color = u_outline_color;
  }
  else if (coords.y > (u_dimensions.y - u_header_height))
  {
    if (coords.y < (u_dimensions.y - u_header_height*.5))
      color = mix(header_color, header_color_gradient, smoothstep(u_dimensions.y - u_header_height*.5, u_dimensions.y - u_header_height, coords.y));
    else
      color = header_color;
  }
  else if (coords.y > (u_dimensions.y - u_header_height - u_line_thickness))
    color = u_line_color;
  else if (coords.y < 2)
    color = header_color;
  //else if (coords.x > (u_dimensions.x - 2) || coords.x < 2) // value precision error in > vs <
  //  color = header_color;

  fragColor = vec4(color, alpha*u_opacity);
}
