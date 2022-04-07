import numpy as np
import pandas as pd
import string
import random


def random_string(min_size, max_size):
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(random.randint(min_size, max_size)))


def random_data_frame():
    size = random.randint(4, 9)
    name1 = random_string(3, 6)
    name2 = random_string(3, 6)
    name3 = random_string(3, 6)

    column1 = np.array([random.randint(10, 234) for _ in range(size)], dtype=np.int32)
    column2 = np.array([random.randint(10, 234) for _ in range(size)], dtype=np.int32)
    column3 = np.array([random_string(10, 20) for _ in range(size)], dtype=object)
    return pd.DataFrame(
        {
            name1: column1,
            name2: column2,
            name3: column3,
        },
    ), f'`{name1}` INT,`{name2}` INT,`{name3}` STRING'



