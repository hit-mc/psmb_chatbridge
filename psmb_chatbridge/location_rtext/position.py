from typing import NamedTuple, Tuple

class Position(NamedTuple):
	x: float
	y: float
	z: float

	@staticmethod
	def fromTuple(t: Tuple[float, float, float]) -> 'Position':
		return Position(x=t[0], y=t[1], z=t[2])