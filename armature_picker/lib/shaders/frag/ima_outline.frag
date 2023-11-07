// @vert_id: IMA

in vec2 texco_interp;
out vec4 fragColor;

uniform sampler2D image;
uniform vec4 u_outline_color;
uniform vec2 u_dimensions;

#define NUM_SAMPLES 8

const vec2 texelSize = 1.0 / u_dimensions;


void main()
{
	vec4 col = texture(image, texco_interp);
	if (col.a > 0.1)
		fragColor = col;
	else {
		vec2 off = 1.0 / u_dimensions;
		float a = texture(image, vec2(texco_interp.x + off.x, texco_interp.y)).a +
			texture(image, vec2(texco_interp.x, texco_interp.y - off.y)).a +
			texture(image, vec2(texco_interp.x - off.x, texco_interp.y)).a +
			texture(image, vec2(texco_interp.x, texco_interp.y + off.y)).a;
		if (col.a < 1.0 && a > 0.0) {
			fragColor = u_outline_color;
			fragColor.a = a;
		}
		else
			fragColor = col;
	}
}
