# Symbolic small signal analysis tool

This tool was created to help with (often lengthy) symbolic small-signal calculations
on circuits. It may be used to verify hand-made calculations, or to completely replace
them. Unfortunately it is still in very early stage, and even though it can calculate most things
symbolically, the results are quite hard to read due to lack of advanced simplification techniques.

It supports passive elements (including inductors and capacitors), dependent current sources,
which is more than enough for most applications -- including transistor circuits.

The small-signal transistor symbol is added to simplify circuit prototyping (rather than manually
adding two resistors (`R_o` and `r_pi`) and dependent source, single three terminal symbol can
be used).

# How to use it?

You need to provide your circuit in a text format to standard input of the `sim.py`. In response
a table will be printed containing all currents and voltages computed in the circuit. It's best
to take a look at the examples.

## Simple example

We wish to calculate the voltage `Vout` with respect to `Vin` as in the image below:

![voltage_divider](https://github.com/sznaider/symsim/blob/master/doc/divider.png)

Of course, we know it is `Vout = R2 / (R1 + R2) * Vin`. To perform calculations with this tool,
we create the following input (let's say, saved to `divider.txt`):

```
Vin 0 a
R1 a out
R2 out 0
```

In this file, we essentially defined a cyclic graph. It has three nodes `0` (which is a reserved
name for ground), `a` and `out`. Edge `(0, a)` is tagged with a voltage source `Vin`, edge `(a,
out)` is tagged with resistor `R1` and so on.

Basically, this is how network definition looks like. Component's first letter defines the type
of a component we wish to add to our circuit. Following letters let us to specify the component's
name (for example: `R1` is a resistor with `1` as its name).

Knowing all of that, we may now run the simulator and get results in form of a table:
```
$ python sim.py < divider.txt
+------------+------------------+
| Quantity   | Value            |
|------------+------------------|
| V(0)       | 0                |
| V(a)       | Vin              |
| V(out)     | R2*Vin/(R1 + R2) |
| I(R1)      | Vin/(R1 + R2)    |
| I(Vin)     | Vin/(R1 + R2)    |
| I(R2)      | Vin/(R1 + R2)    |
+------------+------------------+
```

Unsurprisingly, `Vout` (in the table it's `V(out)`) has the expected value.

## Transistor circuits and small signal analysis

This is where, I think, the tool could be most useful. The small signal analysis of a transistor
circuits is a powerful tool allowing to predict circuit behavior in response to small input
fluctuations.

Naturally, circuit simulators like Spice support small signal analysis. The problem with them
is that they do it by computing circuit's operating point, and to have an actually meaningful
analytical results, one has to simulate circuit along with its entire (and possibly complex)
biasing arrangement, **which is exactly what you don't need to do if you're using this tool**.

This simulator does not determine an operating point. Instead, it outputs transconductances,
Early-effect output resistances and so on, symbolically, leaving their interpretation to the user.

Of course, the family of Spice simulators are accurate, they use complex physical models, and
thus, if your intention is to do a proper circuit analysis, in hope that the circuit works in
real world it'd be best if you used them instead of this tool. This program merely uses a first
order small signal model, as it is currently being teached in most electronics textbooks.

As always, illustrating what it can do, and what it can't, is best illustrated in examples.

### Input / output resistances of a single transistor.

By the way, the tool uses BJT small signal model, because it is the most generic one. If you
wanted to perform calculations for MOSFETs, you simply (for now) must ignore a few things like
finite base resistance in final results and replace them with equivalents for your transistor
(e.g. infinity in case of base resistance).

### Resistance looking into the base of a BJT

![base_resistance](https://github.com/sznaider/symsim/blob/master/doc/input_resistance.png)

To calculate `Req` we'll put a voltage source `Vx` at the base and measure current through
it. (Note that the picture above already shows a small-signal model somewhat superimposed on
the actual circuit).

```
Vx 0 base
Q1 base 0 0

print V(base)/I(Vx)
```

The results are:
```
+---------------+----------+
| Quantity      | Value    |
|---------------+----------|
| V(0)          | 0        |
| V(base)       | Vx       |
| I(Ro_Q1)      | 0        |
| I(Vx)         | Vx/Rp_Q1 |
| I(Rp_Q1)      | Vx/Rp_Q1 |
| V(base)/I(Vx) | Rp_Q1    |
+---------------+----------+
```

and our quantity is calculated to be `Rp_Q1` which is a small-signal base resistance (from
[small signal π model](https://en.wikipedia.org/wiki/Hybrid-pi_model)).

### Resistance looking into the collector and emitter of the BJT

Similarly we can calculate resistance looking into the collector:

![collector_resistance](https://github.com/sznaider/symsim/blob/master/doc/collector_resistance.png)

```
Vx 0 collector
Q1 0 0 collector

print V(collector)/I(Vx)
```

resulting in:

```
+--------------------+----------+
| Quantity           | Value    |
|--------------------+----------|
| V(0)               | 0        |
| V(collector)       | Vx       |
| I(Rp_Q1)           | 0        |
| I(Ro_Q1)           | Vx/Ro_Q1 |
| I(Vx)              | Vx/Ro_Q1 |
| V(collector)/I(Vx) | Ro_Q1    |
+--------------------+----------+
```

And finally, the most interesting is a resistance looking into emitter (which is a parallel
combination of approximately `1/gm` and `R_o`):

![emitter_resistance](https://github.com/sznaider/symsim/blob/master/doc/emitter_resistance.png)

```
Vx 0 emitter
Q1 0 emitter 0

print V(emitter)/I(Vx)
```

resulting in:

```
+------------------+--------------------------------+
| Quantity         | Value                          |
|------------------+--------------------------------|
| V(0)             | 0                              |
| V(emitter)       | Vx                             |
| I(Ro_Q1)         | -Vx/Ro_Q1                      |
| I(Rp_Q1)         | -Vx/Rp_Q1                      |
| I(Vx)            | Gm_Q1*Vx + Vx/Rp_Q1 + Vx/Ro_Q1 |
| V(emitter)/I(Vx) | 1/(Gm_Q1 + 1/Rp_Q1 + 1/Ro_Q1)  |
+------------------+--------------------------------+
```

Here, the result, unfortunately, does not look quite intuitive. It takes a bit of algebra
to see equivalence:
```
1/(Gm_Q1 + 1/Rp_Q1 + 1/Ro_Q1) = 1/(Beta * Gm_Q1 + Gm_Q1) / Beta + 1/Ro_Q1)
= 1/(1/Re_Q1 + 1/Ro_Q1) = (Re_Q1 || Ro_Q1) ~= (1/gm_Q1 || Ro_Q1).
```

### Simple common-emitter amplifier gain calculation

Finally, let's calculate something more interesting. Namely the small-signal gain of the
common-emitter stage:

![common_emitter](https://github.com/sznaider/symsim/blob/master/doc/common_emitter.png)

```
Vin 0 base
Q1 base 0 collector
Rc 0 collector

print V(collector) / Vin
```

which results in:

```
+--------------------+----------------------------------+
| Quantity           | Value                            |
|--------------------+----------------------------------|
| V(0)               | 0                                |
| V(base)            | Vin                              |
| V(collector)       | -Gm_Q1*Rc*Ro_Q1*Vin/(Rc + Ro_Q1) |
| I(Vin)             | Vin/Rp_Q1                        |
| I(Rp_Q1)           | Vin/Rp_Q1                        |
| I(Ro_Q1)           | -Gm_Q1*Rc*Vin/(Rc + Ro_Q1)       |
| I(Rc)              | Gm_Q1*Ro_Q1*Vin/(Rc + Ro_Q1)     |
| V(collector) / Vin | -Gm_Q1*Rc*Ro_Q1/(Rc + Ro_Q1)     |
+--------------------+----------------------------------+
```

in other words, the gain is equal to `-gm * (Rc||ro)`, which is what we expect.

### Gain of the common-emitter with degeneration

In the previous section we did not take into the account the typical arrangement in which a
resistor is added to the emitter of a common-emitter stage for stability and better gain control.

Here's our new circuit to analyze:

![degenerated_common_emitter](https://github.com/sznaider/symsim/blob/master/doc/degenerated_common_emitter.png)

Studying transistor amplifiers, we know that the exact gain formula of such stage can be quite
overwhelming. In any case, we can compute it exactly with this program:

```
Vin 0 base
Q1 base emitter collector
Rc 0 collector
Re emitter 0

print V(collector) / Vin
```

and the results are:
```
...
+--------------------+---------------------------------------------------------------------------------------------------------------------------+
| V(collector) / Vin | Rc*(-Gm_Q1*Ro_Q1*Rp_Q1 + Re)/(Gm_Q1*Re*Ro_Q1*Rp_Q1 + Rc*Re + Rc*Rp_Q1 + Re*Ro_Q1 + Re*Rp_Q1 + Ro_Q1*Rp_Q1)                |
+--------------------+---------------------------------------------------------------------------------------------------------------------------+
```

which indeed does not look friendly. Perhaps in this case the more useful thing would be to
get a gain in a numerical form. We can get numerical results if we provide the values of
components we used in the circuit. This can be achieved with the `set` command.

We may substitute any symbol with a numerical value. In this example, we'll specify all unknowns
to get the gain numerically:

```
Vin 0 base
Q1 base emitter collector
Rc 0 collector
Re emitter 0

# 40mS - typical value when about 1mA is flowing through a collector of a BJT at room temperature
set Gm_Q1 40e-3

# Say the Early voltage is 100, and the current flowing is 1mA
# then Va/Ic gives 100kilo-ohms
set Ro_Q1 100e3

# Now, we specify the transistor's base resistance, assumming Beta = 100, for the results
# to make sense we need to set Rp_Q1 = Beta/gm, thus in this case it need to be 100/40e-3 =
# 2.5kilo-ohms. Admittedly, this is not an ideal way of providing this parameter - something
# to be improved # in the future.
set Rp_Q1 2.5e3

# Let's set some values for Rc and Re. Let Rc=10kOhm, Re=50Ohm. We expect
# the gain of roughly -(Rc||ro)/(Re + 1/gm) ~= -120.
set Rc 10e3
set Re 50

print V(collector) / Vin
```

And, feeding this to the simulator, we get:
```
V(collector) / Vin | -128.101841473179
```

which is close to the result we anticipated.

# All supported components and their definitions

**Definition**: `[name]` used below means a word. That is a sequence of non-whitespace characters.

- Resistors: `R[name] node1 node2`
- Inductors: `L[name] node1 node2`
- Capacitors: `C[name] node1 node2`
- Independent voltage sources: `V[name] node1 node2`
- Independent current sources: `I[name] node1 node2`
- Current controlled current source: `G[name] node1 node2 I(component) scaling-factor`
- Voltage controlled current source: `G[name] node1 node2 V(component) scaling-factor`
- Transistor: `Q[name] base emitter collector optional-'noro' to set ro to infinity`

Some explanations are in order. First of all, whenever we say `I(component)` or `V(component)` it means
the current / voltage at given component. The polarity is determined from component's definition - i.e.
from its `node1` to `node2`.

So, for example `I(R1)`:
```
R1 a b
```
is the current flowing from node `a` to node `b` through resistor `R1`.

And `V(R1)` is the voltage measured as a potential difference between `a` and `b`, that is
`V(a) - V(b)`.

# Print commands

You can tell the simulator to calculate some quantity in addition to all quantities it normally
calculates. The calculated quantity is symbolically manipulated and simplified so that you
don't have to perform tedious algebra on your own. The syntax is supposed to be simple, e.g.:

    print V(out) / Vin

which tells the program to calculate the voltage at node `out` and divde it by the value of
voltage source `Vin`.

# Set commands

Apart from symbolic calculations, sometimes we'd wish to have some real numbers as an output.
Since the results are known symbolically it's just a matter of substituting values. We can
substitute values with `set` commands, e.g.:

    set R1 1000

which sets the `R1` to 1000 ohms. All ocurrences of `R1` are then replaced with `1000`.

# How does it work?

It just solves some nodal equations symbolically with the help of
[SymPy](https://www.sympy.org/en/index.html).

