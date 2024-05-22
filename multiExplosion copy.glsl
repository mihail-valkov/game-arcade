#define MAX_EXPLOSIONS 10

float seed = 0.32; //----------------------------------------------------------starting seed
const float particles = 32.0; //----------------------------------------------change particle count
float res = 256.0; //-----------------------------------------------------------pixel resolution
float gravity = 0.92; //-------------------------------------------------------set gravity
float scale = 0.1; //----------------------------------------------------------scaling factor for explosions

uniform vec2 explodePositions[MAX_EXPLOSIONS]; //------------------------------array of explosion positions
uniform float explodeTimes[MAX_EXPLOSIONS]; //----------------------------------array of explosion times
uniform int numExplosions; //--------------------------------------------------number of active explosions

void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    vec2 normalizedFragCoord = fragCoord / iResolution.xy;
    fragColor = texture(iChannel0, normalizedFragCoord);

    vec2 uv = fragCoord / iResolution.xy;
    float clr = 0.0;

    for (int j = 0; j < numExplosions; j++) {
        float timecycle = iTime - explodeTimes[j];
        if (timecycle < 0.0 || timecycle > 1.0) continue; //---------------------skip inactive explosions

        seed = (seed + floor(explodeTimes[j]));

        vec2 explosionCenter = explodePositions[j] / iResolution.xy;

        float invres = 1.0 / res;
        float invparticles = 1.0 / particles;

        for (float i = 0.0; i < particles; i += 1.0) {
            seed += i + tan(seed);
            vec2 tPos = (vec2(cos(seed), sin(seed))) * i * invparticles; // Apply scaling factor here

            vec2 pPos = explosionCenter;
            pPos += tPos * timecycle;
            pPos.y += -gravity * (timecycle * timecycle) + tPos.y * timecycle;

            pPos = floor(pPos * res) * invres;

            vec2 p1 = pPos;
            vec4 r1 = vec4(vec2(step(p1, uv)), 1.0 - vec2(step(p1 + invres, uv))); // Scale particles
            float px1 = r1.x * r1.y * r1.z * r1.w;
            float px2 = smoothstep(0.0, 250.0, (1.0 / (distance(uv, pPos + .009)))); // Scale glow
            px1 = max(px1, px2);

            clr += px1 * (sin(iTime * 20.0 + i) + 1.0);
        }

        fragColor = mix(fragColor, vec4(clr * (1.0 - timecycle)) * vec4(4, 0.5, 0.1, 1.0), 0.5);
    }
}


void mainImage_old(out vec4 fragColor, in vec2 fragCoord)
{
    vec2 normalizedFragCoord = fragCoord / iResolution.xy;
    fragColor = texture(iChannel0, normalizedFragCoord);

    vec2 uv = (-iResolution.xy + 8*fragCoord.xy) / iResolution.y;
    float clr = 0.0;
    
    for (int j = 0; j < numExplosions; j++) {
        float timecycle = iTime - explodeTimes[j];
        if (timecycle < 0.0 || timecycle > 1.0) continue; //---------------------skip inactive explosions

        seed = (seed + tan(explodeTimes[j]));

        vec2 explosionCenter = explodePositions[j] / iResolution.xy;

        float invres = 1.0 / res;
        float invparticles = 1.0 / particles;

        for (float i = 0.0; i < particles; i += 1.0) {
            seed += i + tan(seed);
            vec2 tPos = (vec2(cos(seed), sin(seed))) * i * invparticles;

            vec2 pPos = explosionCenter;
            pPos.x += ((tPos.x) * timecycle);
            pPos.y += -gravity * (timecycle * timecycle) + tPos.y * timecycle;

            //pPos = floor(pPos * res) * invres;

            vec2 p1 = pPos;
            vec4 r1 = vec4(vec2(step(p1, uv)), 1.0 - vec2(step(p1 + invres, uv)));
            float px1 = r1.x * r1.y * r1.z * r1.w;
            float px2 = smoothstep(0.0, 200.0, (1.0 / distance(uv, pPos + .015)));
            px1 = max(px1, px2);

            clr += px1 * (sin(iTime * 20.0 + i) + 1.0);
        }

        fragColor = mix(fragColor, vec4(clr * (1.0 - timecycle)) * vec4(4, 0.5, 0.1, 1.0), 0.5);
        //fragColor = vec4(clr * (1.0 - timecycle)) * vec4(4, 0.5, 0.1, 1.0);
    }
}
