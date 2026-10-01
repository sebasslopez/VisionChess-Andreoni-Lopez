class Position:
    WIDTH = 100

    def __init__(self, row: int, col: int):
        self.row = row
        self.col = col

    @staticmethod
    def getAlgebraicNotation(row: int, col: int):
        return f"{chr(ord('a') + col)}{8 - row}"

    @staticmethod
    def getFromAlgebraicNotation(pos):
        return Position(8 - int(pos[1]), ord(pos[0].lower()) - ord('a'))

    @staticmethod
    def getFromIndex(index: int):
        return Position(index // 8, index % 8)

    def getTuple(self) -> tuple[int, int]:
        return self.row, self.col

    def isInside(self) -> bool:
        return 0 <= self.row < 8 and 0 <= self.col < 8

    def getXYPosition(self) -> tuple[int, int]:
        return self.col * self.WIDTH, self.row * self.WIDTH

    def getBoundingBox(self):
        x, y = self.getXYPosition()
        return x, y, x + self.WIDTH, y + self.WIDTH

    def isTheSame(self, pos: "Position") -> bool:
        return self == pos

    def __eq__(self, other: object):
        return isinstance(other, Position) and self.row == other.row and self.col == other.col

    def __hash__(self):
        return hash((self.row, self.col))

    @staticmethod
    def getWidth() -> int:
        return Position.WIDTH
