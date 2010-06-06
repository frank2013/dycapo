"""
This file is part of Dycapo.
    Copyright (C) 2009, 2010 FBK Foundation, (http://www.fbk.eu)
    Authors: SoNet Group (see AUTHORS)
    Dycapo is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    Dycapo is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with Dycapo.  If not, see <http://www.gnu.org/licenses/>.

"""
"""
This module holds all the XML-RPC methods that a Driver needs.
"""
import datetime
import models
import response_codes
import rpc4django
import utils

@rpc4django.rpcmethod(name='dycapo.add_trip',
                      signature=['Response', 'Trip', 'Mode', 'Prefs',
                      'Location', 'Location'],
                      permission='server.can_xmlrpc')
def add_trip(trip, mode, preferences, source, destination, ** kwargs):
    """
    DEPRECATED. Use add_trip_exp(Trip trip) instead.
    Inserts a new Trip in Dycapo System. It supports a source, a
    destination and the trip mode. See the models for more information.

    TODO

    - verify user permissions
    - multiple waypoints

    PARAMETERS
    - ``trip`` - a **Trip** object, representing the Trip that the Driver
    is willing to save
    - ``mode`` - a **Mode** object, representing the modalities of the Trip
    - ``preferences`` - a **Prefs** object, representing the Trip preferences
    - ``source`` - a **Location** object, representing where the Trip will
        start.
    - ``destination`` - a **Location** object, representing where the Trip
    will end.

    RETURNS
    An object of type **Response**, containing all the details of the
    operation and results (if any)
    """

    dict_trip = utils.clean_ids(trip)
    dict_mode = utils.clean_ids(mode)
    dict_prefs = utils.clean_ids(preferences)
    dict_source = utils.clean_ids(source)
    dict_destination = utils.clean_ids(destination)

    driver = utils.get_xmlrpc_user(kwargs)

    source = models.Location()
    source = utils.populate_object_from_dictionary(source, dict_source)


    destination = models.Location()
    destination = utils.populate_object_from_dictionary(destination,
                                                        dict_destination)

    mode = models.Mode()
    mode = utils.populate_object_from_dictionary(mode, dict_mode)
    mode.person = driver
    try:
        retrieven_mode = models.Mode.objects.get(person=driver,
                                                 make=mode.make,
                                                 model=mode.model,
                                                 capacity=mode.capacity,
                                                 kind=mode.kind)
        retrieven_mode.vacancy = mode.vacancy
        mode = retrieven_mode

    except models.Mode.DoesNotExist:
        pass

    preferences = models.Prefs()
    preferences = utils.populate_object_from_dictionary(preferences,
                                                        dict_prefs)

    try:
        source.save()
        destination.save()
        mode.save()
        preferences.save()
    except Exception, e:
        resp = models.Response(response_codes.NEGATIVE, str(e), "boolean",
                               False)
        return resp.to_xmlrpc()

    trip = models.Trip()
    trip = utils.populate_object_from_dictionary(trip, dict_trip)
    trip.author = driver
    trip.mode = mode
    trip.prefs = preferences


    try:
        trip.save()
    except Exception, e:
        resp = models.Response(response_codes.NEGATIVE, str(e), "boolean",
                               False)
        return resp.to_xmlrpc()

    trip.locations.add(source)
    trip.locations.add(destination)


    participation = models.Participation(person=driver, trip=trip,
                                         role='driver')
    participation.save()
    trip_stored = models.Trip.objects.get(id=trip.id)
    resp = models.Response(response_codes.POSITIVE,
                           response_codes.TRIP_INSERTED, "Trip",
                           trip_stored.to_xmlrpc())
    return resp.to_xmlrpc()


@rpc4django.rpcmethod(name='dycapo.add_trip_exp',
                      signature=['Response', 'Trip'],
                      permission='server.can_xmlrpc')
def add_trip_exp(trip, ** kwargs):
    """
    Description
    ===========
    
    Inserts a new Trip in Dycapo System. This method does **not** start the
    Trip. use ``start_trip(Trip trip)`` for this scope.

    Permissions
    ===========
    
        * ``user.can_xmlrpc()`` - active by default for all registered users

    Parameters
    ==========
    
        - ``trip`` - a `Trip <http://www.dycapo.org/Protocol#Trip>`_ object,
          representing the Trip that the Driver is saving in Dycapo

    
    Required Parameters Details
    ---------------------------
    
    
    +------------------+-------------------------+-----------------------------+
    | Parameter        | Description             | Type                        |
    +==================+=========================+=============================+
    | trip_            | expires                 | dateTime.iso8601            |
    +------------------+-------------------------+-----------------------------+
    |                  | author                  | struct (Person_)            |
    +------------------+-------------------------+-----------------------------+
    |                  | expires                 | dateTime.iso8601            |
    +------------------+-------------------------+-----------------------------+
    |                  | content                 | struct (Many_)              |
    +------------------+-------------------------+-----------------------------+
    |                  | *content.mode*          | struct (Mode_)              |
    +------------------+-------------------------+-----------------------------+
    |                  | *content.prefs*         | struct (Prefs_)             |
    +------------------+-------------------------+-----------------------------+
    |                  | *content.locations*     | array (Location_)           |
    +------------------+-------------------------+-----------------------------+

    Response Possible Return Values
    -------------------------------
    
    +----------------+---------------------------------------------------------+
    |Response.value  |   Details                                               |
    +================+=========================================================+
    | False          | Something was wrong, look at Response.message           | 
    |                | for details                                             |
    +----------------+---------------------------------------------------------+
    | trip_          | The operation was successful. The returned Trip is the  | 
    |                | one inserted including the id (Trip.id) to be used for  |
    |                | next operations                                         |
    +----------------+---------------------------------------------------------+
    
    .. _Person: http://www.dycapo.org/Protocol#Person
    .. _Many: http://www.dycapo.org/Protocol#Trip
    .. _Mode: http://www.dycapo.org/Protocol#Mode
    .. _Prefs: http://www.dycapo.org/Protocol#Prefs
    .. _Location: http://www.dycapo.org/Protocol#Location

    """

    dict_trip = utils.clean_ids(trip)
    dict_mode = utils.clean_ids(trip["content"]["mode"])
    dict_prefs = utils.clean_ids(trip["content"]["prefs"])
    array_locations = trip["content"]["locations"]

    driver = utils.get_xmlrpc_user(kwargs)

    source = models.Location()
    dict_source = utils.get_location_from_array(array_locations,"orig")
    source = utils.populate_object_from_dictionary(source, dict_source)


    destination = models.Location()
    dict_destination = utils.get_location_from_array(array_locations,"dest")
    destination = utils.populate_object_from_dictionary(destination, dict_destination)

    mode = models.Mode()
    mode = utils.populate_object_from_dictionary(mode, dict_mode)
    vacancy = dict_mode['vacancy']
    preferences = models.Prefs()
    preferences = utils.populate_object_from_dictionary(preferences, dict_prefs)

    mode, created = models.Mode.objects.get_or_create(person=driver,
                                                 make=mode.make,
                                                 model=mode.model,
                                                 capacity=mode.capacity,
                                                 kind=mode.kind)
    mode.vacancy = vacancy

    try:
        source.save()
        destination.save()
        mode.save()
        preferences.save()
    except Exception, e:
        resp = models.Response(response_codes.NEGATIVE, str(e), "boolean",
                               False)
        return resp.to_xmlrpc()

    trip = models.Trip()
    trip = utils.populate_object_from_dictionary(trip, dict_trip)
    trip.author = driver
    trip.mode = mode
    trip.prefs = preferences

    try:
        trip.save()
    except Exception, e:
        resp = models.Response(response_codes.NEGATIVE, str(e), "boolean",
                               False)
        return resp.to_xmlrpc()

    trip.locations.add(source)
    trip.locations.add(destination)

    participation = models.Participation(person=driver, trip=trip,
                                         role='driver')
    participation.save()

    resp = models.Response(response_codes.POSITIVE,
                           response_codes.TRIP_INSERTED, "Trip",
                           trip.to_xmlrpc())

    return resp.to_xmlrpc()

@rpc4django.rpcmethod(name='dycapo.start_trip',
                      signature=['Response', 'Trip'],
                      permission='server.can_xmlrpc')
def start_trip(trip, ** kwargs):
    """
    Starts a Trip

    TODO

    - verify user permissions

    PARAMETERS

    - ``trip`` - a **Trip** object, representing the Trip that the Driver
        is starting

    RETURNS
    An object of type **Response**, containing all the details
    of the operation and results (if any)
    """

    trip_dict = trip
    try:
        trip = models.Trip.objects.only("id","active").get(id=trip_dict['id'])
    except (KeyError, models.Trip.DoesNotExist):
        resp = models.Response(response_codes.NEGATIVE,
                               response_codes.TRIP_NOT_FOUND,
                               "boolean", False)
        return resp.to_xmlrpc()

    participation = models.Participation.objects.get(trip=trip.id,
                                                     role='driver')
    driver = utils.get_xmlrpc_user(kwargs)

    if participation.started:
        resp = models.Response(response_codes.NEGATIVE,
                               response_codes.TRIP_ALREADY_STARTED,
                               "boolean", False)
        return resp.to_xmlrpc()

    participation.started = True
    participation.started_timestamp = datetime.datetime.now()
    try:
        participation.started_position_id = driver.position_id
    except models.Location.DoesNotExist:
        participation.started_position = None
    participation.save()
    trip.active = True
    trip.save()

    resp = models.Response(response_codes.POSITIVE,
                           response_codes.TRIP_STARTED, "boolean", True)
    return resp.to_xmlrpc()


@rpc4django.rpcmethod(name='dycapo.check_ride_requests',
                      signature=['Response', 'Trip'],
                      permission='server.can_xmlrpc')
def check_ride_requests(trip, ** kwargs):
    """
    This method is for a driver to see if there are ride requests
    for his Trip

    TODO

    -verify user permissions

    PARAMETERS

    - ``trip`` - a **Trip** object, representing the Trip that the
    Driver is checking

    RETURNS

    An object of type **Response**, containing all the details of the
    operation and results (if any)
    """

    trip_dict = trip

    try:
        trip = models.Trip.objects.only("id").get(id=trip_dict['id'])
    except (KeyError,models.Trip.DoesNotExist):
        resp = models.Response(response_codes.NEGATIVE,
                               response_codes.TRIP_NOT_FOUND,
                               "Trip", trip_dict)
        return resp.to_xmlrpc()

    driver = utils.get_xmlrpc_user(kwargs)

    participations_for_trip = (models.Participation.objects.filter(trip=trip.id)
                               .exclude(person=driver)
                               .filter(started=False)
                               .filter(finished=False)
                               .filter(requested=True)
                               .filter(requested_deleted=False)
                               ).only("person")

    if not len(participations_for_trip):
        resp = models.Response(response_codes.NEGATIVE,
                               response_codes.RIDE_REQUESTS_NOT_FOUND,
                               "boolean", False)
        return resp.to_xmlrpc()
    else:
        participations = [participation.person.to_xmlrpc()
                          for participation in participations_for_trip]
        resp = models.Response(response_codes.POSITIVE,
                               response_codes.RIDE_REQUESTS_FOUND,
                               "boolean", participations)
        return resp.to_xmlrpc()


@rpc4django.rpcmethod(name='dycapo.accept_ride_request',
                      signature=['Response', 'Trip', 'Person'],
                      permission='server.can_xmlrpc')
def accept_ride_request(trip, person, ** kwargs):
    """
    This method is for a driver to accept a ride request by a rider.

    TODO

    -verify user permissions

    PARAMETERS

    - ``trip`` - a **Trip** object, representing the Trip in which
        the Driver is accepting a ride.
    - ``person`` - a **Person** object, representing the Rider that
        the Driver is accepting

    RETURNS

    An object of type **Response**, containing all the details of the
    operation and results (if any)
    """

    trip_dict = trip
    person_dict = person

    try:
        trip = models.Trip.objects.only("id").get(id=trip_dict['id'])
    except (KeyError, models.Trip.DoesNotExist):
        resp = models.Response(response_codes.NEGATIVE,
                               response_codes.TRIP_NOT_FOUND,
                               "Trip", trip_dict)
        return resp.to_xmlrpc()

    try:
        rider = models.Person.objects.only("id","position").get(
            username=person_dict['username'])
    except (KeyError, models.Person.DoesNotExist):
        resp = models.Response(response_codes.NEGATIVE,
                               response_codes.PERSON_NOT_FOUND,
                               "Person", person_dict)
        return resp.to_xmlrpc()

    try:
        rider_participation = models.Participation.objects.get(trip=trip.id,
                                                               person=rider.id)
    except models.Participation.DoesNotExist:
        resp = models.Response(response_codes.NEGATIVE,
                               response_codes.PERSON_NOT_FOUND,
                               "boolean", False)
        return resp.to_xmlrpc()
    if rider_participation.requested and not rider_participation.accepted:
        rider_participation.accepted = True
        rider_participation.accepted_timestamp = datetime.datetime.now()
        try:
            rider_participation.accepted_position_id = rider.position_id
        except models.Location.DoesNotExist:
            rider_participation.accepted_position = None

        rider_participation.save()
        resp = models.Response(response_codes.POSITIVE,
                               response_codes.RIDE_REQUEST_ACCEPTED,
                               "boolean", True)
        return resp.to_xmlrpc()

    resp = models.Response(response_codes.NEGATIVE,
                           response_codes.RIDE_REQUEST_REFUSED,
                           "boolean", False)
    return resp.to_xmlrpc()


@rpc4django.rpcmethod(name='dycapo.refuse_ride_request',
                      signature=['Response', 'Trip', 'Person'],
                      permission='server.can_xmlrpc')
def refuse_ride_request(trip, person, ** kwargs):
    """
    This method is for a driver to refuse a ride request by a rider.

    TODO

    -verify user permissions

    PARAMETERS

    - ``trip`` - a **Trip** object, representing the Trip in which
        the Driver is refusing a ride.
    - ``person`` - a **Person** object, representing the Rider that
        the Driver is refusing

    RETURNS

    An object of type **Response**, containing all the details of the
    operation and results (if any)
    """

    trip_dict = trip
    person_dict = person

    try:
        trip = models.Trip.objects.only("id").get(id=trip_dict['id'])
    except (KeyError, models.Trip.DoesNotExist):
        resp = models.Response(response_codes.NEGATIVE,
                               response_codes.TRIP_NOT_FOUND,
                               "Trip", trip_dict)
        return resp.to_xmlrpc()

    try:
        rider = models.Person.objects.only("id","position").get(
            username=person_dict['username'])
    except (KeyError, models.Person.DoesNotExist):
        resp = models.Response(response_codes.NEGATIVE,
                               response_codes.PERSON_NOT_FOUND,
                               "Person", person_dict)
        return resp.to_xmlrpc()

    try:
        rider_participation = models.Participation.objects.get(trip=trip.id,
                                                               person=rider.id)
    except models.Participation.DoesNotExist:
        resp = models.Response(response_codes.NEGATIVE,
                           response_codes.PERSON_NOT_FOUND,
                           "boolean", False)
        return resp.to_xmlrpc()


    rider_participation.refused = True
    rider_participation.refused_timestamp = datetime.datetime.now()
    try:
        rider_participation.refused_position_id = rider.position_id
    except models.Location.DoesNotExist:
        rider_participation.accepted_position = None

    rider_participation.save()
    resp = models.Response(response_codes.POSITIVE,
                               response_codes.RIDE_REQUEST_REFUSED,
                               "boolean", True)
    return resp.to_xmlrpc()




@rpc4django.rpcmethod(name='dycapo.finish_trip',
                      signature=['Response', 'Trip'],
                      permission='server.can_xmlrpc')
def finish_trip(trip, ** kwargs):
    """
    This method is for a driver to close a Trip.

    TODO

    -verify user permissions

    PARAMETERS

    - ``trip`` - a **Trip** object, representing the Trip that the driver
    is closing

    RETURNS

    An object of type **Response**, containing all the details of the
    operation and results (if any)
    """

    trip_dict = trip
    trip = models.Trip.objects.only("id").get(id=trip_dict['id'])
    driver = utils.get_xmlrpc_user(kwargs)
    
    if driver.is_participating():
        participation = driver.get_active_participation()
        participation.finished = True
        participation.finished_timestamp = utils.now()
        participation.save()
    trip.active = False
    trip.save()

    resp = models.Response(response_codes.POSITIVE,
                           response_codes.TRIP_DELETED,
                           "boolean", True)
    return resp.to_xmlrpc()
