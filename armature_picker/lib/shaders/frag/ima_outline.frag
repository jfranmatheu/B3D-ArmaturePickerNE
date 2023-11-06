// @vert_id: IMA

in vec2 texco_interp;
out vec4 fragColor;

uniform sampler2D image;
uniform vec4 u_outline_color;
uniform vec2 u_dimensions;
// uniform float u_outline_thickness;

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

/*
void main()
{
    vec4 sumColor = texture(image, texco_interp);

	if (sumColor.a > 0.1)
		fragColor = sumColor;
	else {
		vec2 off = 1.0 / u_dimensions;
		float a = texture(image, vec2(texco_interp.x + texelSize.x, texco_interp.y)).a +
			texture(image, vec2(texco_interp.x, texco_interp.y - texelSize.y)).a +
			texture(image, vec2(texco_interp.x - texelSize.x, texco_interp.y)).a +
			texture(image, vec2(texco_interp.x, texco_interp.y + texelSize.y)).a;
		if (col.a < 1.0 && a > 0.0) {
			for (int i = 0; i < NUM_SAMPLES; i++) {
				vec2 offset = vec2(cos(2.0 * 3.14159265 * float(i) / float(NUM_SAMPLES)), sin(2.0 * 3.14159265 * float(i) / float(NUM_SAMPLES))) * u_outline_thickness;
				sumColor += texture(image, texco_interp + offset * texelSize);
			}

			// Average the colors to smooth the outline
			sumColor /= float(NUM_SAMPLES + 1);

			// Blend the outline color with the averaged color
			fragColor = mix(sumColor, u_outline_color, u_outline_thickness);
		}
		else
			fragColor = sumColor;
	}
}
*/