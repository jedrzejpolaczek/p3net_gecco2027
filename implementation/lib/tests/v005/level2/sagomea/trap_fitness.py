

class ConcatenatedTrap(DummyFitnessFunction):
	'''P3Net level-2 test (v005): concatenated deceptive trap, k = 5, maximised; the
	unitation table of OLyMPuS dec_5 (u = 0..4 -> 4,3,2,1,0; u = 5 -> 5).'''
	def fitness(self, x):
		x = np.array(x).astype(np.int32)
		xStr = self.logger.solutionToStr(x)
		find = self.logger.returnSolution(xStr)
		if find != None:
			return find
		table = [4, 3, 2, 1, 0, 5]
		score = float(sum(table[int(np.sum(x[i:i + 5]))] for i in range(0, len(x), 5)))
		self.logger.write(xStr, score)
		self.logger.writeForTraining(xStr, score)
		return score
