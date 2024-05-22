float seed = 0.32; //----------------------------------------------------------starting seed
const float particles = 32.0; //----------------------------------------------change particle count
float res = 32.0; //-----------------------------------------------------------pixel resolution
float gravity = 0.72; //-------------------------------------------------------set gravity

uniform vec2 explodePosition; //------------------------------------------------explosion position

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    vec2 normalizedFragCoord = fragCoord / iResolution.xy;
    fragColor = texture(iChannel0, normalizedFragCoord);

    if (explodePosition.x == 0.0 && explodePosition.y == 0.0)
    {
        return;
    }

    vec2 uv = (-iResolution.xy + 2.0 * fragCoord.xy) / iResolution.y;
    float clr = 0.0;  
    float timecycle = iTime - floor(iTime);  
    seed = (seed + floor(iTime));
    
    // Adjust explosion center to normalized coordinates
    vec2 explosionCenter = explodePosition / iResolution.xy;

    float invres = 1.0 / res;
    float invparticles = 1.0 / particles;

    for (float i = 0.0; i < particles; i += 1.0)
    {
        seed += i + tan(seed);
        vec2 tPos = (vec2(cos(seed), sin(seed))) * i * invparticles;
        
        vec2 pPos = explosionCenter; //--------------------------------------------start at explosion center
        pPos.x += ((tPos.x) * timecycle);
        pPos.y += -gravity * (timecycle * timecycle) + tPos.y * timecycle;

        pPos = floor(pPos * res) * invres; //--------------------------------------comment this out for smooth version 

        vec2 p1 = pPos;
        vec4 r1 = vec4(vec2(step(p1, uv)), 1.0 - vec2(step(p1 + invres, uv)));
        float px1 = r1.x * r1.y * r1.z * r1.w;
        float px2 = smoothstep(0.0, 200.0, (1.0 / distance(uv, pPos + .015))); //added glow
        px1 = max(px1, px2);

        clr += px1 * (sin(iTime * 20.0 + i) + 1.0);
    }

    fragColor = mix(fragColor, vec4(clr * (1.0 - timecycle)) * vec4(4, 0.5, 0.1, 1.0), 1);
}
