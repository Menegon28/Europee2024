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






