europee <- read.csv("~/Uni/Sde 2/Progetto/VotiPerc_R.csv", header=TRUE)
attach(europee)
y <- FRATELLI.D.ITALIA/100
mod.1 <- lm(y ~ log(ELETTORI))
summary(mod.1)
plot(y ~ log(ELETTORI))
Beta <- coef(mod.1)
abline(Beta[1], Beta[2], col="red")

plot(y/100 ~ log(ELETTORI))
logitc <- log((y + 0.5/ELETTORI)/ (1- y +0.5/ ELETTORI))
glm.1 <- glm(y ~ ELETTORI, family=binomial, weights=ELETTORI)
summary(glm.1)
logitc
library(GGally)
library(ggplot2)

head(europee)
x <- as.matrix(europee[,7:14])
rownames(x) <- europee[,4]
head(x)
pc <- prcomp(x, scale=T, center=T)
plot(pc, type="l")
cumsum(pc$sdev/sum(pc$sdev))
biplot(pc, xlabs=rep("*",dim(x)[1]))
factanal(x, 4)
ggpairs(europee[,7:14], 
        lower = list(continuous = "points"),   # Scatterplot for lower part
        upper = list(continuous = "cor"),     # Correlation values for upper part
        diag = list(continuous = "density"))  # Density plots on the diagonal



dist_matrix <- dist(x, method = "euclidean")
hc <- hclust(dist_matrix, method = "ward.D2")
plot(hc,cex=0.1)
rect.hclust(hc, k = 100)  # Cut into 3 clusters
# Cut the dendrogram into clusters
cluster_assignments <- cutree(hc, k = 100)  # Assume 3 clusters
print(cluster_assignments["BASSANO DEL GRAPPA"])               # Print all cluster assignments

# To print members of a specific cluster (e.g., cluster 2):
cluster_2 <- x[cluster_assignments == 30, ]
print(sort(rownames(cluster_2)))


detach()


europeeAbs <- read.csv("~/Uni/Sde 2/Progetto/VotiAbs_R.csv", header=TRUE)
attach(europeeAbs)
y <- FRATELLI.D.ITALIA
mod.1 <- lm(y ~ ELETTORI)
summary(mod.1)
plot(y ~ ELETTORI)
Beta <- coef(mod.1)
abline(Beta[1], Beta[2], col="red")

plot(y ~ log(ELETTORI))
glm.1 <- glm(cbind(y, VOTI_VALIDI - y) ~ ELETTORI, family=binomial)
summary(glm.1)






