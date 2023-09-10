// @vert_id: IMA

in vec2 texco_interp;
out vec4 fragColor;
uniform sampler2D image;
uniform float o;
void main()
{
    vec2 fragCoord = gl_FragCoord.xy;
    fragColor = texture(image, texco_interp);
    fragColor.a *= o;
}