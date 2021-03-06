from cell import Cell

class Sudoku:
    def __init__(self, debug=False):
        self.debug = debug
        self.cells = self.initCells()
        self.hasChanged = False

    def initCells(self):
        cells = []
        for y in range(9):
            for x in range(9):
                cells.append(Cell(y,x))
        return cells
    
    def getCell(self, y, x):
        for cell in self.cells:
            if (cell.x == x and cell.y == y):
                return cell
    
    def getCellsInRegion(self, id):
        return [cell for cell in self.cells if cell.regionID == id] 

    def getCellsInRow(self, y):
        return [cell for cell in self.cells if cell.y == y]

    def getCellsInColumn(self, x):
        return [cell for cell in self.cells if cell.x == x]

    def isSolved(self):
        solved = True
        for cell in self.cells:
            if (not cell.isSet()):
                solved = False
        return solved

    def absoluteEntry(self, value, y, x):
        cell = self.getCell(y, x)
        cell.makeAbsolute(value)

    def textToAbsolutes(self, text):
        if (len(text) != 81):
            print("ERROR: String must consist of exactly 81 characters. Current length:", len(text))
            print("Loading aborted.")
            return
        for char in text:
            if (char not in ".123456789"):
                print("ERROR: String can only consist of numbers 1-9 and periods for blank spaces.")
                print("Loading aborted.")
                return
        y = 0
        x = 0
        for char in text:
            if (char != "."): #Periods represent blanks.
                self.absoluteEntry(int(char), y, x)
            if (y == 8 and x == 8):
                clues = len([char for char in text if char != "."])
                if (self.debug):
                    print("Sudoku loading complete.", clues, "clues.")
                return
            if (x == 8):
                y += 1
            x = (x+1)%9
    
    def absolutesToText(self):
        payload = ""
        for y in range(9):
            for x in range(9):
                payload += str(self.getCell(y,x).getValue())
        return payload

    def debugCell(self, cell):
        print("Cell", cell.y, cell.x, "| RegionID:", cell.regionID, "| Candidates:", cell.candidates)

    def debugCellAt(self, y, x):
        cell = self.getCell(y, x)
        self.debugCell(cell)
    
    def debugCells(self, cells):
        for cell in cells:
            self.debugCell(cell)

    def printSudoku(self):
        payload = ""
        for y in range(9):
            for x in range(9):
                cell = self.getCell(y, x)
                if (cell.isSet() == True):
                    payload += str(cell.getValue()) + " "
                else:
                    payload += ". "
                if (x == 2 or x == 5):
                    payload += "│ "
            if (y == 2 or y == 5):
                payload += "\n──────┼───────┼──────"
            if (y != 8):
                payload += "\n"
        print(payload)

    def compareToAbsolutes(self):
        for cell in self.cells:
            if cell.isSet():
                continue
            newCandidates = []
            for candidate in cell.candidates:
                if (self.isValidNumber(cell, candidate)):
                    newCandidates.append(candidate)
            if (cell.candidates != newCandidates and len(newCandidates) == 1):
                self.solvedCellMsg("Absolute", cell.y, cell.x, newCandidates[0])
                self.hasChanged = True
            cell.candidates = newCandidates
            if (len(cell.candidates) < 1):
                print("ERROR: Cell", cell.y, cell.x, "has zero candidates left.")

    def isValidNumber(self, cell, attemptedValue):
        if (self.positionConflict(cell, attemptedValue, lambda c1,c2:c1.x==c2.x)): return False
        if (self.positionConflict(cell, attemptedValue, lambda c1,c2:c1.y==c2.y)): return False
        if (self.positionConflict(cell, attemptedValue, lambda c1,c2:c1.regionID==c2.regionID)): return False
        return True

    def positionConflict(self, c1, attemptedValue, conflictType):
        for c2 in self.cells:
            if (not c2.isSet()):
                continue
            if (c1 == c2):
                continue
            if (conflictType(c1, c2) and attemptedValue == c2.getValue()):
                return True
    
    def isGroupComplete(self, cellGroup):
        groupCompleted = True
        for cell in cellGroup:
            if (not cell.isSet()):
                groupCompleted = False
        return groupCompleted

    def compareToCandidates(self, cellGroupGetter):
        # Compare itself with other cells in same Region to determine if a certain number can only be here.
        for i in range(9): # ID of each Region, row, or column. 0-8.
            cellGroup = cellGroupGetter(i) #Collect all cells in the Region of that ID.
            
            #Disprove that the group is already complete. If complete, continue with next index.
            if (self.isGroupComplete(cellGroup)):
                continue

            for nr in range(1,9+1): # Each theoretically possible number entry in a cell. 1-9.
                validCells = []
                for cell in cellGroup:
                    if (nr in cell.candidates):
                        validCells.append(cell)
                if (len(validCells) == 1 and not validCells[0].isSet()):
                    validCells[0].makeAbsolute(nr) #Remove all candidates of cell except for "nr"! Cell solved!
                    self.solvedCellMsg(cellGroupGetter.__name__, validCells[0].y, validCells[0].x, nr)
                    self.hasChanged = True

    def eliminateFromAxis(self): #Removes candidates from both axis by method of elimination.
        #For each number not yet set in Region:
        #   If all cells that has that number as a candidate is in same row or column:
        #       Eliminate that number as candidate from each other cell on that axis, but outside that region.
        for regionID in range(9): #RegionID 0-8
            cellRegion = self.getCellsInRegion(regionID)
            if (self.isGroupComplete(cellRegion)):
                continue

            for nr in range(1,9+1): #Possible value of a cell. 1-9.
                #Check if nr is already set within region. If so, skip this nr.
                nrSetInRegion = False
                for cell in cellRegion:
                    if (cell.isSet() and cell.getValue() == nr):
                        nrSetInRegion = True
                if (nrSetInRegion):
                    continue
                
                #Gather all unset cells with nr as a candidate.
                cellsWithCandidate = []
                for cell in cellRegion:
                    if (nr in cell.candidates and not cell.isSet()):
                        cellsWithCandidate.append(cell)
                
                # Only proceed if two or more cells are found.
                if (len(cellsWithCandidate) < 2):
                    continue
                
                #If all cells found share the same axis,
                # remove nr as candidate from cells on that axis outside this region.
                allInRow = True
                allInColumn = True
                yAxis = cellsWithCandidate[0].y
                xAxis = cellsWithCandidate[0].x
                for cell in cellsWithCandidate:
                    if (cell.y != yAxis):
                        allInRow = False
                    if (cell.x != xAxis):
                        allInColumn = False
                if (allInRow):
                    self.eliminateCandidateFromAxisOutsideRegion(nr, regionID, yAxis, self.getCellsInRow)
                if (allInColumn):
                    self.eliminateCandidateFromAxisOutsideRegion(nr, regionID, xAxis, self.getCellsInColumn)


    def eliminateCandidateFromAxisOutsideRegion(self, nr, regionID, axisIndex, cellGroupGetter):
        for cell in cellGroupGetter(axisIndex):
            if (cell.regionID == regionID):
                continue
            if (nr in cell.candidates and not cell.isSet()):
                self.eliminatedCandMsg("AxisElimination", cell.y, cell.x, nr)
                cell.candidates.remove(nr)
                if (cell.isSet()):
                    self.solvedCellMsg("AxisElimination", cell.y, cell.x, cell.getValue())
                    self.hasChanged = True


    def solveByExhaustion(self):
        for y in range(9):
            for x in range(9):
                cell = self.getCell(y,x)
                if not cell.isSet():
                    for candidate in cell.candidates:
                        if self.isValidNumber(cell, candidate):
                            candidateStorage = cell.candidates.copy() #To preserve a list smaller than [1..9]
                            cell.makeAbsolute(candidate)
                            self.solveByExhaustion()
                            if self.isSolved():
                                return
                            cell.candidates = candidateStorage
                    return


    def solvedCellMsg(self, strategy, y, x, val):
        if (self.debug):
            print("SOLVING with [Comp("+strategy+")]: Cell", y, x, "has been set to", val)
    
    def eliminatedCandMsg(self, strategy, y, x, val):
        if (self.debug):
            print("SOLVING with [Comp("+strategy+")]: Cell", y, x, "has lost candidate", val)


    def solve(self):
        iterations = 0
        
        if (self.debug):
            self.printSudoku()
            input("PRESS ENTER TO ITERATE")

        while(True):
            iterations += 1
            self.hasChanged = False #To be proven True by the following solving functions.
            self.compareToAbsolutes()
            self.compareToCandidates(self.getCellsInRegion)
            self.compareToCandidates(self.getCellsInRow)
            self.compareToCandidates(self.getCellsInColumn)
            self.eliminateFromAxis()
            
            if not self.hasChanged:
                if (self.debug):
                    print("UNABLE TO CONTINUE REASONING")
                    print("EXHAUSTING REMAINING POSSIBILITIES")
                self.solveByExhaustion()
            
            if (self.isSolved()):
                if (self.debug):
                    self.printSudoku()
                    print("SUDOKU SOLVED IN", iterations, "ITERATIONS")
                break