
from mcdreforged.api.all import ServerInterface, RColor, RText, RTextList, RAction
from .position import Position
from .dimension import get_dimension, Dimension


def coordinate_text(x: float, y: float, z: float, dimension: Dimension):
    coord = RText('[{}, {}, {}]'.format(int(x), int(y), int(z)),
                  dimension.get_coordinate_color())
    return coord.h(dimension.get_rtext())


def location(name: str, position: Position, dimension_str: str) -> RTextList:
    x, y, z = position
    dimension = get_dimension(dimension_str)

    # basic text: someone @ dimension [x, y, z]
    texts = RTextList(RText(name, RColor.yellow), ' @ ',
                      dimension.get_rtext(), ' ', coordinate_text(x, y, z, dimension))
    texts.append(' ', RText('[+V]', RColor.aqua).h('§bVoxelmap§r: 点此以高亮坐标点, 或者Ctrl点击添加路径点').c(
        RAction.run_command, '/newWaypoint x:{}, y:{}, z:{}, dim:{}'.format(
            int(x), int(y), int(z), dimension.get_reg_key()
        )
    ))

    if dimension.has_opposite():
        oppo_dim, oppo_pos = dimension.get_opposite(position)
        arrow = RText('->', RColor.gray)
        texts.append(RText.format(
            ' {} {}',
            arrow.copy().h(RText.format('{} {} {}', dimension.get_rtext(), arrow, oppo_dim.get_rtext())),
            coordinate_text(oppo_pos.x, oppo_pos.y, oppo_pos.z, oppo_dim)
        ))

    return texts
