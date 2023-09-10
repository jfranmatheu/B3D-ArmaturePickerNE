uniform mat4 ModelViewProjectionMatrix;
in vec2 pos;

void main()
{
    gl_Position = ModelViewProjectionMatrix * vec4(pos, 1.0f, 1.0f);
}