uniform vec4 u_color;

in vec2 uv;
out vec4 fragColor;


// Varying variables to pass vertices to the fragment shader
in vec2 v0;
in vec2 v1;
in vec2 v2;


float calculateDistanceToEdge(vec2 pos, vec2 v00, vec2 v01)
{
    vec2 v0v1 = v01 - v00;
    vec2 v0p = pos - v00;

    float edgeLength = length(v0v1);
    float edgeDistance = abs(cross(vec3(v0v1, 0.0), vec3(v0p, 0.0)).z) / edgeLength;

    return edgeDistance;
}


float drawPolygon(vec2 pos)
{
    // Calculate the signed distance to the edges of the polygon
    float distanceToEdges = 1.0;

    float edgeDistance0 = calculateDistanceToEdge(pos, v0, v1);
    float edgeDistance1 = calculateDistanceToEdge(pos, v1, v2);
    float edgeDistance2 = calculateDistanceToEdge(pos, v2, v0);

    distanceToEdges = min(distanceToEdges, min(edgeDistance0, min(edgeDistance1, edgeDistance2)));

    return distanceToEdges;
}


void main()
{
    fragColor = u_color;

    // You can use any shape drawing logic here.
    float shape = drawPolygon(uv);

    // Anti-aliasing based on distance field.
    float edgeWidth = 0.02; // Adjust the edge width for smoother or sharper edges.
    float alpha = smoothstep(0.5 - edgeWidth, 0.5 + edgeWidth, shape);

    // Final color with alpha blending.
    fragColor = vec4(fragColor.rgb, fragColor.a * alpha);
}
