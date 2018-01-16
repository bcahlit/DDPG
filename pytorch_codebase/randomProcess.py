import numpy as np
import matplotlib.pyplot as plt


class RandomProcess:

    def reset_states(self):
        pass


class AnnealedGaussianProcess(object):

    def __init__(self, mu, sigma, sigma_min, n_steps_annealing):
        self.mu = mu
        self.sigma = sigma
        self.n_steps = 0

        if sigma_min is not None:
            self.m = -float(sigma - sigma_min) / float(n_steps_annealing)
            self.c = sigma
            self.sigma_min = sigma_min
        else:
            self.m = 0.
            self.c = sigma
            self.sigma_min = sigma

    @property
    def current_sigma(self):
        sigma = max(self.sigma_min, self.m * float(self.n_steps) + self.c)
        return sigma


class OrnsteinUhlenbeckProcess(AnnealedGaussianProcess):

    def __init__(self, theta, mu=0., sigma=0.2,
                 dt=1e-2, x0=None, size=1,
                 sigma_min=None, n_steps_annealing=1000):
        super(OrnsteinUhlenbeckProcess,
              self).__init__(mu=mu,
                             sigma=sigma,
                             sigma_min=sigma_min,
                             n_steps_annealing=n_steps_annealing)
        self.theta = theta
        self.mu = mu
        self.dt = dt
        self.x0 = x0
        self.size = size
        self.reset_states()

    def sample(self):
        x = self.x_prev + \
            self.theta * (self.mu -
                          self.x_prev) * self.dt + (
                              self.current_sigma * np.sqrt(self.dt) *
                              np.random.normal(size=self.size)
            )
        self.x_prev = x
        self.n_steps += 1
        return x

    def reset_states(self):
        self.x_prev = self.x0 if self.x0 is not None else np.zeros(self.size)


if __name__ == "__main__":
    o = OrnsteinUhlenbeckProcess(theta=1.0)
    o.reset_states()
    r = []
    for i in range(10000000):
        s = o.sample()
        r.append(float(s[0]))
    plt.plot(r)
    plt.savefig("test_OU")
    plt.close()
