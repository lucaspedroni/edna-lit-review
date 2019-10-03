library(ggplot2)

data1 <- read.csv("years", header=FALSE, col.names=c("Year", "Mentions"))

tiff("mentions_by_year.tiff", units="in", width=5, height=4, res=300)
p <- ggplot(data1, aes(x=Year, y=Mentions)) + geom_bar(stat="identity", alpha=.8, fill="dodgerblue2", color="dodgerblue2")
p <- p + scale_x_continuous(breaks=seq(1991, 2019, 4))
p
dev.off()

