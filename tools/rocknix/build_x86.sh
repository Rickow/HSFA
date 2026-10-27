#!/bin/bash
# Temoin x86_64 : memes sources et memes options que la compilation ROCKNIX (sauf -mcpu), pour comparer les captures
set -e
SUB=${1:-hsfa}
D=${HSFA_WORKSPACE}/work/agent_rocknix
cd $D/fbneo_x86/src/burner/libretro
ARGS=(platform=unix SUBSET=$SUB "PLATFORM_DEFINES=-O2 -U__FAST_MATH__")
nice -n 19 make "${ARGS[@]}" clean-objs >/dev/null
nice -n 19 make -j4 "${ARGS[@]}" REGEN_HEADERS=1
