#!/bin/bash
# (agent_hyper_etats) tournee_hyper.lua : tournee.sh <nom> ; variables LISTE, MODEJEU (1|4), NF, SNAPM, MODEFORCE
export SCRIPT=${HSFA_WORKSPACE}/work/agent_hyper_etats/lua/tournee_hyper.lua
exec ${HSFA_WORKSPACE}/work/agent_hyper_etats/lance.sh "$@"
