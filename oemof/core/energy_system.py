# -*- coding: utf-8 -*-
"""
Created on Mon Jul 20 15:53:14 2015

@author: uwe
"""

import logging
from oemof.core.network import Entity
from oemof.core.network.entities.components import transports as transport
from oemof.solph.optimization_model import OptimizationModel as OM


class EnergySystem:
    r"""Defining an energy supply system to use oemof's solver libraries.

    Note
    ----
    The list of regions is not necessary to use the energy system with solph.

    Parameters
    ----------
    entities : list of core.network objects
        List of all objects of the energy system. All class descriptions can
        be found in the :py:mod:`oemof.core.network` package.
    simulation : core.energy_system.Simulation object
        Simulation object that contains all necessary attributes to start the
        solver library. Defined in the :py:class:`Simulation
        <oemof.core.energy_system.Simulation>` class.
    regions : list of core.energy_system.Region objects
        List of regions defined in the :py:class:`Region
        <oemof.core.energy_system.Simulation>` class.
    year : integer
        Define the time for the energy system.

    Attributes
    ----------
    entities : list of core.network objects
        List of all objects of the energy system. All class descriptions can
        be found in the :py:mod:`oemof.core.network` package.
    simulation : core.energy_system.Simulation object
        Simulation object that contains all necessary attributes to start the
        solver library. Defined in the :py:class:`Simulation
        <oemof.core.energy_system.Simulation>` class.
    regions : list of core.energy_system.Region objects
        List of regions defined in the :py:class:`Region
        <oemof.core.energy_system.Simulation>` class.
    """
    def __init__(self, **kwargs):
        for attribute in ['regions', 'entities', 'simulation']:
            setattr(self, attribute, kwargs.get(attribute, []))
        Entity.registry = self
        self.optimization_model = kwargs.get('optimization_model', None)
        self.year = kwargs.get('year')

    # TODO: Condense signature (use Buse)
    def connect(self, bus1, bus2, in_max, out_max, eta, transport_class):
        """Create two transport objects to connect two buses of the same type
        in both directions.

        Parameters
        ----------
        bus1, bus2 : core.network.Bus object
            Two buses to be connected.
        eta : float
            Constant efficiency of the transport.
        in_max : float
            Maximum input the transport can handle, in $MW$.
        out_max : float
            Maximum output which can possibly be obtained when using the
            transport, in $MW$.
        transport_class class
            Transport class to use for the connection
        """
        if not transport_class == transport.Simple:
            logging.error('')
            raise(TypeError(
                "Sorry, `EnergySystem.connect` currently only works with" +
                "a `transport_class` argument of" + str(transport.Simple)))
        for bus_a, bus_b in [(bus1, bus2), (bus2, bus1)]:
            uid = bus_a.uid + bus_b.uid
            transport_class(uid=uid, outputs=[bus_a], inputs=[bus_b],
                            out_max=[out_max], in_max=[in_max], eta=[eta])

    # TODO: Add concept to make it possible to use another solver library.
    def optimize(self):
        """Start optimizing the energy system using solph."""
        if self.optimization_model is None:
            self.optimization_model = OM(energysystem=self)

        self.optimization_model.solve(solver=self.simulation.solver,
                                      debug=self.simulation.debug,
                                      tee=self.simulation.stream_solver_output,
                                      duals=self.simulation.duals)


class Region:
    r"""Defining a region within an energy supply system.

    Note
    ----
    The list of regions is not necessary to use the energy system with solph.

    Parameters
    ----------
    entities : list of core.network objects
        List of all objects of the energy system. All class descriptions can
        be found in the :py:mod:`oemof.core.network` package.
    name : string
        A unique name to identify the region. If possible use typical names for
        regions and english names for countries.
    code : string
        A short unique name to identify the region.
    geom : shapely.geometry object
        The geometry representing the region must be a polygon or a multi
        polygon.

    Attributes
    ----------
    entities : list of core.network objects
        List of all objects of the energy system. All class descriptions can
        be found in the :py:mod:`oemof.core.network` package.
    name : string
        A unique name to identify the region. If possible use typical names for
        regions and english names for countries.
    geom : shapely.geometry object
        The geometry representing the region must be a polygon or a multi
        polygon.
    """
    def __init__(self, **kwargs):
        self.entities = []  # list of entities
        self.add_entities(kwargs.get('entities', []))

        self.name = kwargs.get('name')
        self.geom = kwargs.get('geom')
        self._code = kwargs.get('code')

    # TODO: oder sollte das ein setter sein? Yupp.
    def add_entities(self, entities):
        """Add a list of entities to the existing list of entities.

        For every entity added to a region the region attribute of the entity
        is set

        Parameters
        ----------
        entities : list of core.network objects
            List of all objects of the energy system that belongs to area
            covered by the polygon of the region. All class descriptions can
            be found in the :py:mod:`oemof.core.network` package.
        """

        # TODO: prevent duplicate entries
        self.entities.extend(entities)
        for entity in entities:
            if self not in entity.regions:
                entity.regions.append(self)

    @property
    def code(self):
        """Creating a short code based on the region name if no code is set."""
        if self._code is None:
            name_parts = self.name.replace('_', ' ').split(' ', 1)
            self._code = ''
            for part in name_parts:
                self._code += part[:1].upper() + part[1:3]
        return self._code


class Simulation:
    r"""Defining the simulation related parameters according to the solver lib.

    Parameters
    ----------
    solver : string
        Name of the solver supported by the used solver library.
        (e.g. 'glpk', 'gurobi')
    debug : boolean
        Set the chosen solver to debug (verbose) mode to get more information.
    stream_solver_output : boolean
        If True, solver output is streamed in python console
    duals : boolean
        If True, results of dual variables and reduced costs will be saved
    objective_options : dictionary
        'function': function to use from
                    :py:mod:`oemof.solph.predefined_objectives`
        'cost_objects': list of str(`class`) elements. Objects of type  `class`
                        are include in cost terms of objective function.
        'revenue_objects': list of str(`class`) elements. . Objects of type
                           `class` are include in revenue terms of
                           objective function.
    timesteps : list or sequence object
         Timesteps to be simulated or optimized in the used library
    """
    def __init__(self, **kwargs):
        ''
        self.solver = kwargs.get('solver', 'glpk')
        self.debug = kwargs.get('debug', False)
        self.stream_solver_output = kwargs.get('stream_solver_output', False)
        self.objective_options = kwargs.get('objective_options', {})
        self.duals = kwargs.get('duals', False)
        self.timesteps = kwargs.get('timesteps')
        if self.timesteps is None:
            raise ValueError('No timesteps defined!')
