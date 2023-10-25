
// VERT_ID: ADVANCE_POINT_GRAPHIC

const float PI = 3.14159265358979323846264;
const float SQRT_2 = 1.4142135623730951;

out vec4 fragColor;

uniform float u_size, u_linewidth, u_antialias;
uniform vec4 u_fg_color, u_bg_color;

uniform vec2 u_rotation;
// varying vec2 rotation;
// varying vec2 v_size;


// Computes the signed distance from a line
float line_distance(vec2 p, vec2 p1, vec2 p2) {
    vec2 center = (p1 + p2) * 0.5;
    float len = length(p2 - p1);
    vec2 dir = (p2 - p1) / len;
    vec2 rel_p = p - center;
    return dot(rel_p, vec2(dir.y, -dir.x));
}


// Computes the signed distance from a line segment
float segment_distance(vec2 p, vec2 p1, vec2 p2) {
    vec2 center = (p1 + p2) * 0.5;
    float len = length(p2 - p1);
    vec2 dir = (p2 - p1) / len;
    vec2 rel_p = p - center;
    float dist1 = abs(dot(rel_p, vec2(dir.y, -dir.x)));
    float dist2 = abs(dot(rel_p, dir)) - 0.5*len;
    return max(dist1, dist2);
}


// Computes the centers of a circle with
// given radius passing through p1 & p2
vec4 inscribed_circle(vec2 p1, vec2 p2, float radius)
{
    float q = length(p2-p1);
    vec2 m = (p1+p2)/2.0;
    vec2 d = vec2( sqrt(radius*radius - (q*q/4.0)) * (p1.y-p2.y)/q,
    sqrt(radius*radius - (q*q/4.0)) * (p2.x-p1.x)/q);
    return vec4(m+d, m-d);
}


// ----------------------------------------------------------------


float arrow_angle(vec2 texcoord, float body, float head, float height, float linewidth, float antialias)
{
    float d;
    float w = linewidth/2.0 + antialias;
    vec2 start = -vec2(body/2.0, 0.0);
    vec2 end = +vec2(body/2.0, 0.0);

    // Arrow tip (beyond segment end)
    if ( texcoord.x > body/2.0) {
        // Head : 2 segments
        float d1 = line_distance(texcoord,
        end, end - head*vec2(+1.0,-height));
        float d2 = line_distance(texcoord,
        end - head*vec2(+1.0,+height), end);
        // Body : 1 segment
        float d3 = end.x - texcoord.x;
        d = max(max(d1,d2), d3);
    }   
    else {
        // Head : 2 segments
        float d1 = segment_distance(texcoord,
        end - head*vec2(+1.0,-height), end);
        float d2 = segment_distance(texcoord,
        end - head*vec2(+1.0,+height), end);
        // Body : 1 segment
        float d3 = segment_distance(texcoord,
        start, end - vec2(linewidth,0.0));
        d = min(min(d1,d2), d3);
    }

    return d;
}


// ----------------------------------------------------------------


float square(vec2 P, float size)
{
    return max(abs(P.x), abs(P.y)) - size/(2.0*SQRT_2);
}

float disc(vec2 P, float size)
{
    return length(P) - size/2;
}

float triangle(vec2 P, float size)
{
    float x = SQRT_2/2.0 * (P.x - P.y);
    float y = SQRT_2/2.0 * (P.x + P.y);
    float r1 = max(abs(x), abs(y)) - size/(2*SQRT_2);
    float r2 = P.y;
    return max(r1,r2);
}

float diamond(vec2 P, float size)
{
    float x = SQRT_2/2.0 * (P.x - P.y);
    float y = SQRT_2/2.0 * (P.x + P.y);
    return max(abs(x), abs(y)) - size/(2.0*SQRT_2);
}

float heart(vec2 P, float size)
{
    float x = SQRT_2/2.0 * (P.x - P.y);
    float y = SQRT_2/2.0 * (P.x + P.y);
    float r1 = max(abs(x),abs(y))-size/3.5;
    float r2 = length(P - SQRT_2/2.0*vec2(+1.0,-1.0)*size/3.5)
    - size/3.5;
    float r3 = length(P - SQRT_2/2.0*vec2(-1.0,-1.0)*size/3.5)
    - size/3.5;
    return min(min(r1,r2),r3);
}

float chevron(vec2 P, float size)
{
    float x = 1.0/SQRT_2 * (P.x - P.y);
    float y = 1.0/SQRT_2 * (P.x + P.y);
    float r1 = max(abs(x), abs(y)) - size/3.0;
    float r2 = max(abs(x-size/3.0), abs(y-size/3.0)) - size/3.0;
    return max(r1,-r2);
}

float ring(vec2 P, float size)
{
    float r1 = length(P) - size/2.0;
    float r2 = length(P) - size/4.0;
    return max(r1,-r2);
}

float tag(vec2 P, float size)
{
    float r1 = max(abs(P.x)- size/2.0, abs(P.y)- size/6.0);
    float r2 = abs(P.x-size/1.5)+abs(P.y)-size;
    return max(r1,0.75*r2);
}

float cross(vec2 P, float size)
{
    float x = SQRT_2/2.0 * (P.x - P.y);
    float y = SQRT_2/2.0 * (P.x + P.y);
    float r1 = max(abs(x - size/3.0), abs(x + size/3.0));
    float r2 = max(abs(y - size/3.0), abs(y + size/3.0));
    float r3 = max(abs(x), abs(y));
    return max(min(r1,r2),r3) - size/2.0;
}

float asterisk(vec2 P, float size)
{
    float x = SQRT_2/2.0 * (P.x - P.y);
    float y = SQRT_2/2.0 * (P.x + P.y);
    float r1 = max(abs(x)- size/2.0, abs(y)- size/10.0);
    float r2 = max(abs(y)- size/2.0, abs(x)- size/10.0);
    float r3 = max(abs(P.x)- size/2.0, abs(P.y)- size/10.0);
    float r4 = max(abs(P.y)- size/2.0, abs(P.x)- size/10.0);
    return min( min(r1,r2), min(r3,r4));
}

float infinity(vec2 P, float size)
{
    const vec2 c1 = vec2(+0.2125, 0.00);
    const vec2 c2 = vec2(-0.2125, 0.00);
    float r1 = length(P-c1*size) - size/3.5;
    float r2 = length(P-c1*size) - size/7.5;
    float r3 = length(P-c2*size) - size/3.5;
    float r4 = length(P-c2*size) - size/7.5;
    return min( max(r1,-r2), max(r3,-r4));
}

float pin(vec2 P, float size) {
    vec2 c1 = vec2(0.0,-0.15)*size;
    float r1 = length(P-c1)-size/2.675;
    vec2 c2 = vec2(+1.49,-0.80)*size;
    float r2 = length(P-c2) - 2.*size;
    vec2 c3 = vec2(-1.49,-0.80)*size;
    float r3 = length(P-c3) - 2.*size;
    float r4 = length(P-c1)-size/5;
    return max( min(r1,max(max(r2,r3),-P.y)), -r4);
}



// ----------------------------------------------------------------


float arrow(vec2 P, float size)
{
    float x = P.x;
    float y = P.y;
    float r1 = abs(x) + abs(y) - size/2;
    float r2 = max(abs(x+size/2), abs(y)) - size/2;
    float r3 = max(abs(x-size/6)-size/4, abs(y)- size/4);
    return min(r3,max(.75*r1,r2));
}

float arrow_angle_90(vec2 texcoord, float body, float head, float linewidth, float antialias)
{
    return arrow_angle(texcoord, body, head, 1.00, linewidth, antialias);
}


// ----------------------------------------------------------------


vec4 stroke(
    float distance, // Signed distance to line
    float linewidth, // Stroke line width
    float antialias, // Stroke antialiased area
    vec4 stroke_color) // Stroke color
{
    float t = linewidth / 2.0 - antialias;
    float signed_distance = distance;
    float border_distance = abs(signed_distance) - t;
    float alpha = border_distance / antialias;
    alpha = exp(-alpha * alpha);
    if( border_distance < 0.0 )
        return stroke_color;
    else
        return vec4(stroke_color.rgb, stroke_color.a * alpha);
}


vec4 filled(
    float distance, // Signed distance to line
    float linewidth, // Stroke line width
    float antialias, // Stroke antialiased area
    vec4 fill) // Fill color
{
    float t = linewidth / 2.0 - antialias;
    float signed_distance = distance;
    float border_distance = abs(signed_distance) - t;
    float alpha = border_distance / antialias;
    alpha = exp(-alpha * alpha);
    if( border_distance < 0.0 )
        return fill;
    else if( signed_distance < 0.0 )
        return fill;
    else
        return vec4(fill.rgb, alpha * fill.a);
}


vec4 outline(
    float distance, // Signed distance to line
    float linewidth, // Stroke line width
    float antialias, // Stroke antialiased area
    vec4 stroke, // Stroke color
    vec4 fill) // Fill color
{
    float t = linewidth / 2.0 - antialias;
    float signed_distance = distance;
    float border_distance = abs(signed_distance) - t;
    float alpha = border_distance / antialias;
    alpha = exp(-alpha * alpha);
    if( border_distance < 0.0 )
        return stroke;
    else if( signed_distance < 0.0 )
        return mix(fill, stroke, sqrt(alpha));
    else
        return vec4(stroke.rgb, stroke.a * alpha);
}


// ----------------------------------------------------------------

void main()
{
    vec2 P = gl_PointCoord.xy - vec2(0.5, 0.5);
    P = vec2(u_rotation.x*P.x - u_rotation.y*P.y,
             u_rotation.y*P.x + u_rotation.x*P.y);
    // float d = marker(P*v_size, size);
    // u_body == u_size, u_head == u_body * 0.15
    float d = arrow_angle_90(P*u_size, u_size, u_size * 0.15, u_linewidth, u_antialias);
    fragColor = outline(d, u_linewidth, u_antialias, u_fg_color, u_bg_color);
}
