uniform vec4 co;
out vec4 fragColor;
void main()
{
  fragColor = co;
  fragColor = blender_srgb_to_framebuffer_space(fragColor);
}