#define MAX_EXPLOSIONS 10

float seed = 0.32; // starting seed
const float size1_Particles = 33.0; // change particle count
float res = 1.0; // pixel resolution
float gravity = 0.92; // set gravity
float scale = 1.0; // scaling factor for explosions

uniform vec2 explodePositions[MAX_EXPLOSIONS]; // array of explosion positions
uniform float explosionSizes[MAX_EXPLOSIONS]; // array of explosion positions
uniform float explodeTimes[MAX_EXPLOSIONS]; // array of explosion times
uniform int numExplosions; // number of active explosions


float rand(vec2 co) {
    return fract(sin(dot(co.xy, vec2(12.9898, 78.233))) * 43758.5453);
}

vec2 hash(vec2 p) {
    p = vec2(dot(p, vec2(127.1, 311.7)),
            dot(p, vec2(269.5, 183.3)));
    return -1.0 + 2.0 * fract(sin(p) * 43758.5453123);
}

vec2 Hash12_Polar(float t) {
    float a = fract(sin(t * 674.3) * 453.2) * 6.2832;
    float d = fract(sin((t + a) * 714.3) * 263.2);
    return vec2(sin(a), cos(a)) * d;
}

float explosion(vec2 uv, float time, float size) {
    float sparks = 0.0;
    float particles = size1_Particles * size;
    for (float i = 0.0; i < particles; i++) {
        vec2 dir = Hash12_Polar(i + 1.); //*.2
        dir.y -= (gravity / 3.) * time;
        float d = length(uv - dir * time * 0.1 * size);
        float brightness = mix(0.0005, 0.002, smoothstep(0.05, 0.0, time));
        brightness *= sin(time * 20.0 + i) * 0.5 + 0.5;
        brightness *= smoothstep(1., 0.5, time);
        sparks += brightness / d;
    }
    return sparks;
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec4 texColor = texture(iChannel0, uv);

    if (numExplosions == 0) 
    {
        fragColor = texColor;
        return;
    }

    vec4 explosionColor = vec4(0.0);

    for (int i = 0; i < numExplosions; i++) {
        vec2 explodePosition = explodePositions[i];
        float explodeTime = explodeTimes[i];
        float explosionSize = explosionSizes[i]; // assuming x component represents the size

        if (explosionSize == 0.) {
            explosionSize = 1.;
        }

        explodeTime = iTime - explodeTime;

        vec2 center = explodePosition / iResolution.xy;
        vec2 pos = (fragCoord - explodePosition) / res;
        float dist = length(pos);
        float angle = atan(pos.y, pos.x);

        vec2 explosionCenter = (fragCoord - center * iResolution.xy) / iResolution.y;
        
        vec3 col = vec3(0.0);
        col += explosion(explosionCenter, explodeTime, explosionSize) *
            vec3(1., smoothstep(0.647, 0.0, explodeTime), smoothstep(0.3, 0.0, explodeTime)); // orange to red

        col *= scale;
        explosionColor += vec4(col, 1.0);
    }

    fragColor = texColor + explosionColor;
}
