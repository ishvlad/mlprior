import math


############################################
# Mapping from 'color_name' to 'RGB color' #
############################################

class _color:
    def __init__(self, colors):
        for k, v in colors.items():
            setattr(self, k, v)

    def get_colors_code(self, num=-1):
        all_colors = list(set(self.__dict__.values()))

        if num == -1:
            return all_colors
        elif num <= len(all_colors):
            return all_colors[:num]
        else:
            return (all_colors * math.ceil(num/len(all_colors)))[:num]


GLOBAL__CATEGORIES = {
    "cs.AI": "Artificial Intelligence",
    "cs.CC": "Computational Complexity",
    "cs.CG": "Computational Geometry",
    "cs.CE": "Computational Engineering, Finance, and Science",
    "cs.CL": "Computation and Language",
    "cs.CV": "Computer Vision and Pattern Recognition",
    "cs.CY": "Computers and Society",
    "cs.CR": "Cryptography and Security",
    "cs.DB": "Databases",
    "cs.DS": "Data Structures and Algorithms",
    "cs.DL": "Digital Libraries",
    "cs.DM": "Discrete Mathematics",
    "cs.DC": "Distributed, Parallel, and Cluster Computing",
    "cs.ET": "Emerging Technologies",
    "cs.FL": "Formal Languages and Automata Theory",
    "cs.GT": "Computer Science and Game Theory",
    "cs.GL": "General Literature",
    "cs.GR": "Graphics",
    "cs.AR": "Hardware Architecture",
    "cs.HC": "Human-Computer Interaction",
    "cs.IR": "Information Retrieval",
    "cs.IT": "Information Theory",
    "cs.LG": "Machine Learning",
    "cs.LO": "Logic in Computer Science",
    "cs.MS": "Mathematical Software",
    "cs.MA": "Multiagent Systems",
    "cs.MM": "Multimedia",
    "cs.NI": "Networking and Internet Architecture",
    "cs.NE": "Neural and Evolutionary Computation",
    "cs.NA": "Numerical Analysis",
    "cs.OS": "Operating Systems",
    "cs.OH": "Other",
    "cs.PF": "Performance",
    "cs.PL": "Programming Languages",
    "cs.RO": "Robotics",
    "cs.SI": "Social and Information Networks",
    "cs.SE": "Software Engineering",
    "cs.SD": "Sound",
    "cs.SC": "Symbolic Computation",
    "cs.SY": "Systems and Control"
}
GLOBAL__COLORS = _color({
    'sb_blue':      '#4e73df',
    'sb_cyan':      '#36b9cc',
    'sb_gray':      '#858796',
    'sb_green':     '#1cc88a',
    'sb_indigo':    '#6610f2',
    'sb_orange':    '#fd7e14',
    'sb_pink':      '#e83e8c',
    'sb_purple':    '#6f42c1',
    'sb_red':       '#e74a3b',
    'sb_teal':      '#20c9a6',
    'sb_yellow':    '#f6c23e',
})

VISUALIZATION__INITIAL_NUM_BARS = 12
