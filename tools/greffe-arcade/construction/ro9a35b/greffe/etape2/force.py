# DECISIONS IMPOSEES du plan de greffe (etape 2) : routine d'Upper -> ('HYPER', homologue) | ('GREFFE',) | ('NATIF', x)
FORCE = {
    0x4EA30: ('SYNTH', 'depart_arcade'),   # depart de partie (lanceur ARCADE) : tache Arcade d'Upper 0x1346A0 creee,
                                     # puis depart commun d'Hyper 0x63560 (init, tache de jeu ; versions, $A9...)
    0x24F020: ('HYPER', 0xA49E0),    # choix du decor : celui d'Hyper (decors d'Hyper par version, numeros 0/2/4) tant
                                     # que les decors d'Upper ne sont pas importes (DECORS.md §2.3, alternative minimale)
    0x265750: ('HYPER', 0x9A980),    # init de manche : celle d'Hyper (versions ; Upper n'y ajoute que DRAMATIC et $17A)
    0x16CA80: ('GREFFE',),           # moteur des objets ($FF8000+ : table des types 0x615100) appele par les scenes
                                     # Arcade : celui d'Upper, avec SA table des types (le type 14 d'Hyper est un autre
                                     # objet) ; les entrees equivalentes renvoient aux gestionnaires d'Hyper
}
