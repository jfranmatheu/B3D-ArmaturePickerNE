uniform mat4 ModelViewProjectionMatrix;

in vec2 pos;
in vec2 texco;
out vec2 uv;

void main()
{
  uv = texco;
  gl_Position = (ModelViewProjectionMatrix * vec4(pos, 1.0f, 1.0f));
}