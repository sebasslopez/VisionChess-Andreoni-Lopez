from __future__ import annotations
from .Box import Box
from .Color import Color
from .Position import Position
import pygame
from .pieces.Pawn import Pawn
from .pieces.Bishop import Bishop
from .pieces.King import King
from .pieces.Queen import Queen
from .pieces.Knight import Knight
from .pieces.Rook import Rook
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .pieces.Piece import Piece

class Board:
    DEFAULT_BOARD = "rnbqkbnrpppppppp................................PPPPPPPPRNBQKBNR"

    def __init__(self,flag:bool,board=DEFAULT_BOARD, turns:bool = True):
        if not isinstance(board, str) or len(board) != 64:
            board = self.DEFAULT_BOARD
        self.initial = board
        self.actual = board
        self.changeHistory = []
        self.boxes:list[Box] = []
        self.Pieces:list[Piece] = []
        self.board:list[list[Box]] = self.createBoard(False, board)
        self.capturedPieces:list[Piece] = []
        self.isUpsideDown = False
        self.isSelected = False
        self.SelectedBox = None
        self.finished = False
        self.turns = turns
        self.turn = Color.WHITE
        self.last_move = None
        self.kings:list[King] = []
        self.kingsBox:list[Box] = self.getKings()
        if flag: self.previewBoard = self.copyBoard()
    

    def display(self,window: pygame.Surface):
        display_board = getattr(self, "previewBoard", self)
        for b in display_board.boxes:
            if isinstance(b.piece, King):
                b.colorAC = b.COLOROG
                if King.check(b.position, self, b.piece.color):
                    b.colorAC = Color.RED
            b.display(window)

    def createBoard(self,flag:bool, board:str|None = None) -> list[list[Box]]:
        result:list[list[Box]] = []
        for i in range(0,8):
            row:list[Box] = []
            for j in range(0,8):
                piece = None if board is None else board[i * 8 + j]
                p: Piece | None = Board.createPiece(i,j,flag, piece)
                b: Box = Box(p,self.getBoxColor(i,j),Position(i,j))
                row.append(b)
                self.boxes.append(b)
                if p is not None: self.Pieces.append(p)
            result.append(row)
        return result

    @staticmethod
    def getBoxColor(row:int,column:int) -> Color:
        return Color.WHITE if ((row+column) % 2) == 0 else Color.BLACK

    def getBox(self,position: Position) -> Box | None:
        pos:tuple[int,int] = position.getTuple()
        if not position.isInside(): return None
        return self.board[pos[0]][pos[1]]

    def getOpositePieces(self,color:Color) -> list[Piece]:
        l:list[Piece] = []
        for p in self.Pieces:
            if p.color != color:
                l.append(p)
        return l
    


    @staticmethod
    def createPiece(row: int,column:int,flag:bool,piece=None)-> Piece | None:
        if piece is not None:
            piece_types = {"p": Pawn, "b": Bishop, "k": King, "q": Queen, "n": Knight, "r": Rook}
            piece_type = piece_types.get(str(piece).lower())
            if piece_type is None or piece == ".":
                return None
            color = Color.WHITE if str(piece).isupper() else Color.BLACK
            return piece_type(color, Position(row,column))
        return Board.getDefaulPieceByPos(row,column,Board.getColorByPos(row,column,flag))

    def updateBoard(self, new_board: str) -> list[str]:
        if not isinstance(new_board, str) or len(new_board) != 64:
            return []
        changes = []
        for index, (current, new) in enumerate(zip(self.actual, new_board)):
            if current != new:
                changes.append((index, Position(index // 8, index % 8), current, new))
        if not changes:
            return []

        confirmed = []
        confirmed_changes = []
        castling = self._getCastlingChange(changes)
        if castling is not None:
            change_list, record = castling
            confirmed_changes.extend(change_list)
            confirmed.append(record)
        else:
            for source in changes:
                source_index, source_position, source_char, source_new = source
                if source_char == "." or source_new != ".":
                    continue
                source_box = self.getBox(source_position)
                if source_box is None or source_box.piece is None:
                    continue
                for target in changes:
                    target_index, target_position, target_char, target_new = target
                    promotion = (isinstance(source_box.piece, Pawn)
                                 and target_position.row in (0, 7)
                                 and target_new.lower() in ("q", "r", "b", "n"))
                    if (target_index == source_index or target_new == "."
                            or (target_new != source_char and not promotion)):
                        continue
                    if target_char != "." and target_char.isupper() == source_char.isupper():
                        continue
                    if not source_box.piece.isMoveValid(target_position, self):
                        continue
                    if promotion:
                        confirmed_changes.extend((source, target))
                        confirmed.append(f"{Position.getAlgebraicNotation(source_position.row, source_position.col)}p{target_new.lower()}")
                    else:
                        confirmed_changes.extend((source, target))
                        confirmed.append(f"{Position.getAlgebraicNotation(source_position.row, source_position.col)}m{Position.getAlgebraicNotation(target_position.row, target_position.col)}")
                    break
                if confirmed:
                    break

        if not confirmed:
            return []
        updated = list(self.actual)
        for index, _, _, new in confirmed_changes:
            updated[index] = new
        self.actual = "".join(updated)
        self.changeHistory.extend(confirmed)
        self._loadBoard(self.actual)
        if self.turns:
            self.turn = Color.BLACK if self.turn == Color.WHITE else Color.WHITE
        self.finished = self.checkFinished()
        return confirmed

    def _getCastlingChange(self, changes):
        for king_change in changes:
            king_index, king_position, king_char, king_new = king_change
            if king_char.lower() != "k" or king_new != ".":
                continue
            king_box = self.getBox(king_position)
            if king_box is None or not isinstance(king_box.piece, King):
                continue
            for king_target_change in changes:
                target_index, king_target, target_char, target_new = king_target_change
                if (target_char != "." or target_new != king_char
                        or king_target.row != king_position.row
                        or abs(king_target.col - king_position.col) != 2):
                    continue
                rook_column = 0 if king_target.col < king_position.col else 7
                rook_target_column = 3 if rook_column == 0 else 5
                rook_position = Position(king_position.row, rook_column)
                rook_target = Position(king_position.row, rook_target_column)
                rook_source_change = None
                rook_target_change = None
                for change in changes:
                    if change[1].isTheSame(rook_position):
                        rook_source_change = change
                    if change[1].isTheSame(rook_target):
                        rook_target_change = change
                rook_box = self.getBox(rook_position)
                if (rook_source_change is None or rook_target_change is None
                        or rook_box is None or not isinstance(rook_box.piece, Rook)
                        or rook_source_change[2] != ("R" if king_char.isupper() else "r")
                        or rook_source_change[3] != "."
                        or rook_target_change[2] != "."
                        or rook_target_change[3] != rook_source_change[2]
                        or not king_box.piece.isMoveValid(king_target, self)):
                    continue
                return ([king_change, king_target_change, rook_source_change, rook_target_change], f"{Position.getAlgebraicNotation(king_position.row, king_position.col)}c{Position.getAlgebraicNotation(king_target.row, king_target.col)}")
        return None

    def _loadBoard(self, board: str):
        self.boxes = []
        self.Pieces = []
        self.capturedPieces = []
        self.board = self.createBoard(False, board)
        self.kings = []
        self.kingsBox = self.getKings()
        self.last_move = None
        self.isSelected = False
        self.SelectedBox = None
        if hasattr(self, "previewBoard"):
            self.previewBoard = self.copyBoard()

    @staticmethod
    def getColorByPos(row: int,column:int,flag:bool) -> Color:
        if row * 8 + column <=32:
            return Color.WHITE if flag else Color.BLACK
        return Color.BLACK if flag else Color.WHITE

    @staticmethod
    def getDefaulPieceByPos(row: int,column:int,color:Color) -> Piece | None:
        if row == 1 or row == 6:
            return Pawn(color,Position(row,column))
        elif row == 0 or row == 7:
            if column == 0  or column == 7:
                return Rook(color,Position(row,column))
            elif column == 1 or column == 6:
                return Knight(color,Position(row,column))
            elif column == 2 or column == 5:
                return Bishop(color,Position(row,column))
            elif column == 3:
                return Queen(color,Position(row,column))
            else:
                return King(color,Position(row,column))
        return None

    def verifyClick(self,rect:tuple[int,int]):
        if self.finished: return
        b = self.getClickedBox(rect)
        if b is None: return
        if not self.isSelected:
            if b.piece is None: return
            if self.turns and b.piece.color != self.turn: return
            self.previewBoard = self.copyBoard()
            self.SelectedBox = b
            self.isSelected = True
            self.previewBoard.board = b.makePreviewBoard(self.previewBoard)
        else:
            if self.SelectedBox is None or self.SelectedBox.piece is None:
                self.SelectedBox = None
                self.isSelected = False
                return
            if (b.isEmpty() or (b.isoccupied() and not self.SelectedBox.piece.isTeamMate(b.piece))) and not isinstance(b.piece, King) and self.SelectedBox.piece.isMoveValid(b.position, self):
                self.SelectedBox.piece.move(b,self)
                self.SelectedBox.clearPiece()
                self.SelectedBox = None
                self.isSelected = False
                self.previewBoard = self.copyBoard()
                if self.turns:
                    self.turn = Color.BLACK if self.turn == Color.WHITE else Color.WHITE
                if self.checkFinished(): 
                    self.finished = True
                    print("JUEGO FINALIZADO!!!!!!!")
            elif b.piece is not None and b.isoccupied() and b.piece.isTeamMate(self.SelectedBox.piece):
                self.previewBoard = self.copyBoard()
                self.SelectedBox = b
                self.isSelected = True
                self.previewBoard.board = b.makePreviewBoard(self.previewBoard)


    def getKings(self):
        l: list[Box] = []
        for b in self.boxes:
            if isinstance(b.piece, King):
                l.append(b)
                self.kings.append(b.piece)
        return l

    def checkFinished(self):
        if len(self.kings) < 2:
            return False
        return self.kings[0].isCheckMate(self) or self.kings[1].isCheckMate(self) or self.londonBridgeFellDown() or self.checkQuantity()

    def londonBridgeFellDown(self):
        return self.kings[0].isCaptured or self.kings[1].isCaptured

    def checkQuantity(self):
        return not self.getOpositePieces(Color.WHITE) or not self.getOpositePieces(Color.BLACK)
    
    def copyBoard(self) -> Board:
        bor: Board = Board(False)
        bor.board = []
        bor.boxes = []
        bor.capturedPieces = []
        bor.Pieces = []
        for s in self.board:
            row: list[Box] = []
            for t in s:
                b = Box(t.piece,t.COLOROG,t.position)
                row.append(b)
                bor.boxes.append(b)
            bor.board.append(row)
        for s in self.Pieces:
                    bor.Pieces.append(s)
        for s in self.capturedPieces:
                    bor.capturedPieces.append(s)
        bor.kings = []
        bor.kingsBox = bor.getKings()
        bor.isUpsideDown = self.isUpsideDown
        bor.isSelected = self.isSelected
        bor.SelectedBox = self.SelectedBox
        bor.turns = self.turns
        bor.turn = self.turn
        bor.last_move = self.last_move
        bor.initial = self.initial
        bor.actual = self.actual
        bor.changeHistory = self.changeHistory.copy()
        bor.finished = self.finished
        return bor
            

    def getClickedBox(self,rect:tuple[int,int])-> "Box | None":
        for b in self.boxes:
            if b.clickInside(rect):
                return b
        return None
                        
