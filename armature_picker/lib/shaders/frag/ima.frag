// @vert_id: IMA

in vec2 texco_interp;
out vec4 fragColor;
uniform sampler2D image;
void main()
{
    fragColor = texture(image, texco_interp);
}