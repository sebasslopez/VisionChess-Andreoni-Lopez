class Position:
    OFFSET_X = 0
    OFFSET_Y = 0

    def __init__(self, row: int, col: int):
        self.row = row
        self.col = col
        self.WIDTH:int = self.getWidth()

    @staticmethod
    def getAlgebraicNotation(row: int, col: int):
        return chr(col + 97) + str(8 - row)

    def getTuple(self)-> tuple[int,int] :
        return (self.row,self.col)

    def isInside(self) -> bool:
        return self.row < 8 and self.row > -1 and self.col < 8 and self.col > -1

    def getXYPosition(self) -> tuple[int,int]:
        return ((self.col * self.WIDTH + Position.OFFSET_X), (self.row * self.WIDTH + Position.OFFSET_Y))

    def getBoundingBox(self):
        Axes = self.getXYPosition()
        return (Axes[0], Axes[1], self.WIDTH, self.WIDTH)

    def isTheSame(self,pos: "Position") -> bool:
        return pos.getXYPosition()[0] == self.getXYPosition()[0] and pos.getXYPosition()[1] == self.getXYPosition()[1]

    def __eq__(self,other:object):
        return isinstance(other,Position) and self.isTheSame(other)


    @staticmethod
    def getWidth() ->int:
        return 100
