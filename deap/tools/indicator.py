import numpy
import moocore


def hypervolume(front, **kargs):
    """Returns the index of the individual with the least the hypervolume
    contribution. The provided *front* should be a set of non-dominated
    individuals having each a :attr:`fitness` attribute.

    The hypervolume is computed using the `moocore` package.
    See :func:`moocore.hypervolume` for details.
    """
    # Must use wvalues * -1 since hypervolume use implicit minimization
    # And minimization in deap use max on -obj
    wobj = numpy.array([ind.fitness.wvalues for ind in front]) * -1
    ref = kargs.get("ref", None)
    if ref is None:
        ref = numpy.max(wobj, axis=0) + 1

    def contribution(i):
        # The contribution of point p_i in point set P
        # is the hypervolume of P without p_i
        return moocore.hypervolume(numpy.concatenate((wobj[:i], wobj[i + 1:])), ref=ref)

    # Parallelization note: Cannot pickle local function
    contrib_values = [contribution(i) for i in range(len(front))]

    # Select the maximum hypervolume value (correspond to the minimum difference)
    return numpy.argmax(contrib_values)


__all__ = ["hypervolume"]
