uniform vec4 u_color;
out vec4 fragColor;
void main()
{
  fragColor = u_color;
  // fragColor = blender_srgb_to_framebuffer_space(fragColor);
}