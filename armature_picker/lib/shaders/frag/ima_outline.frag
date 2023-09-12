// @vert_id: IMA

in vec2 texco_interp;
out vec4 fragColor;

uniform sampler2D image;
uniform vec4 u_outline_color;

const float offset = 1.0 / 128.0;


void main()
{
	vec4 col = texture(image, texco_interp);
	if (col.a > 0.1)
		fragColor = col;
	else {
		float a = texture(image, vec2(texco_interp.x + offset, texco_interp.y)).a +
			texture(image, vec2(texco_interp.x, texco_interp.y - offset)).a +
			texture(image, vec2(texco_interp.x - offset, texco_interp.y)).a +
			texture(image, vec2(texco_interp.x, texco_interp.y + offset)).a;
		if (col.a < 1.0 && a > 0.0)
			fragColor = u_outline_color;
		else
			fragColor = col;
	}
}
