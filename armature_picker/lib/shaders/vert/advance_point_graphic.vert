uniform mat4 ModelViewProjectionMatrix; // ortho
uniform float u_size, u_orientation, u_linewidth, u_antialias;
in vec2 pos;
varying vec2 rotation;
varying vec2 v_size;

const float SQRT_2 = 1.4142135623730951;

void main (void)
{
    rotation = vec2(cos(u_orientation), sin(u_orientation));
    gl_Position = ModelViewProjectionMatrix * vec4(pos, 1.0f, 1.0f); // ortho * vec4(position, 1.0);
    v_size = SQRT_2 * u_size + 2.0*(u_linewidth + 1.5*u_antialias);
    gl_PointSize = v_size;
}
