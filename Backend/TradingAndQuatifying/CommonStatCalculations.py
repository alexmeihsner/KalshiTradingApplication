class StatCalculations:
    def __init__(self, currentOdds: float):
        self.__currentOdds = currentOdds
        self.__expectedValue
        self.__americanOdds
        self.__optimalBetSize

    def implied_probability_to_american(self, currentOdds: float) -> float:
        if currentOdds < 0.5:
            decimalOdds = (100 / currentOdds)
            americanOdds = decimalOdds - 100
            self.__americanOdds = americanOdds
            return americanOdds
        else:
            americanOdds = (-(100* currentOdds) / (1-currentOdds))
            self.__americanOdds = americanOdds
            return americanOdds

    def american_to_decimal(self, americanOdds: float ) -> float:
        if americanOdds > 0:
            return 1 + (americanOdds / 100)
        else:
            return 1 + (100 / abs(americanOdds))

    def american_to_net(self, american_odds: float) -> float:
        return self.american_to_decimal(american_odds) - 1

    def expected_value(self, prob: float, odds: float, stake: float = 1.0) -> float:
        b = self.american_to_net(odds)
        ev = (prob * b * stake) - ((1 - prob) * stake)
        self.__expected_value = ev
        return ev

    #optimal bet size
    def kelly_criterion(self) -> float:
        probOfWinning = self.__currentOdds
        probOfLoss = 1- probOfWinning
        netOdds = self.american_to_net(self.__americanOdds)
        optimalBetSize = ((netOdds * probOfWinning) - probOfLoss) / netOdds
        #puts odds to zero if it is negative
        optimalBetSize = max(0.0, optimalBetSize)
        self.__optimalBetSize = optimalBetSize
        return optimalBetSize


