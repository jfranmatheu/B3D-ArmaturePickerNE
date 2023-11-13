uniform mat4 ModelViewProjectionMatrix;
in vec2 pos;
layout(location = 1) in vec2 pos_rel;
out vec2 uv;

void main()
{
    uv = pos_rel;
    gl_Position = ModelViewProjectionMatrix * vec4(pos, 1.0f, 1.0f);
}