from typing import Any


src2palam_map: dict[str, dict[str, dict[str, Any]]] = {
    'c_pleasure_source': {
        # 快C
        'c_pleasure_palam': {
            'chara': 'target',
            'value': 1.0
        }
    },
    'v_pleasure_source': {
        # 快V
        'v_pleasure_palam': {
            'chara': 'target',
            'value': 1.0
        }
    },
    'a_pleasure_source': {
        # 快A
        'a_pleasure_palam': {
            'chara': 'target',
            'value': 1.0
        }
    },
    'b_pleasure_source': {
        # 快B
        'b_pleasure_palam': {
            'chara': 'target',
            'value': 1.0
        }
    },
    'm_pleasure_source': {
        # 快M
        'm_pleasure_palam': {
            'chara': 'target',
            'value': 1.0
        }
    },
    'happiness_source': {
        # 欢乐
        'kindness_palam': {
            'chara': 'target',
            'value': 1.0
        }
    },
    'conquest_source': {
        # 征服
        'submission_palam': {
            'chara': 'target',
            'value': 1.0
        }
    },
    'passivity_source': {
        # 被动
        'superiority_palam': {
            'chara': 'target',
            'value': 1.0
        },
        'submission_palam': {
            'chara': 'source',
            'value': 0.5
        },
        'obedience_palam': {
            'chara': 'source',
            'value': 0.5
        },
    }
}