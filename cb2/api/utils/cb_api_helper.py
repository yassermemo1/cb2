import logging
import traceback
import uuid
import csv
import io
from cbapi.response import CbResponseAPI, Sensor
from cbapi.protection import CbProtectionAPI, Computer
from cbapi.errors import ServerError, ApiError, CredentialError
from ..models import CBInstance, Agent, db
from flask import current_app

logger = logging.getLogger(__name__)

class CBAPIHelper:
    """Helper class to interact with Carbon Black API."""
    
    @staticmethod
    def test_connection(cb_instance, skip_test=False):
        """
        Test connection to a Carbon Black server and update connection status
        
        Args:
            cb_instance: The CBInstance object containing connection details
            skip_test: If True, skip the actual connection test (for debugging)
            
        Returns:
            dict: Connection result with keys 'status', 'message', and 'version'
        """
        try:
            logger.info(f"Testing connection to {cb_instance.name} ({cb_instance.api_base_url})")
            
            # For debugging/testing purposes
            if skip_test:
                logger.warning(f"Skipping connection test for {cb_instance.name} (debug mode)")
                cb_instance.update_connection_status('Connected (test skipped)', 'Test skipped for debugging')
                return {'status': 'Connected', 'message': 'Test skipped for debugging', 'version': 'Unknown'}
            
            # Get the CB API client
            cb_api = CBAPIHelper.get_cb_api(cb_instance)
            if not cb_api:
                error_msg = f"Failed to initialize API client for {cb_instance.name}"
                logger.error(error_msg)
                cb_instance.update_connection_status("Failed to initialize API", error_msg)
                return {'status': 'Failed to initialize API', 'message': error_msg, 'version': 'Unknown'}
                
            # Get the connection credentials
            credentials = cb_instance.to_credential_dict()
            logger.debug(f"Using credentials: url={credentials['url']}, ssl_verify={credentials['ssl_verify']}")
            
            # Initialize CB API based on server type - default to Response API
            logger.info(f"Initializing CbResponseAPI for {cb_instance.name}")
            cb_api = CbResponseAPI(**credentials)
            
            # Simple test query to verify connection
            try:
                sensors = list(cb_api.select(Sensor).all()[:1])
                logger.info(f"Successfully connected to {cb_instance.name}, found {len(sensors)} sensors")
                
                # Update sensors count if we got any
                cb_instance.sensors = len(cb_api.select(Sensor).all())
            except Exception as e:
                logger.error(f"Error querying sensors: {str(e)}")
                raise
            
            # Update instance status
            cb_instance.update_connection_status('Connected', 'Successfully connected')
            # Try to get version information
            version = 'Unknown'
            try:
                info = cb_api.info()
                if hasattr(info, 'version'):
                    version = info.version
            except:
                pass
                
            return {'status': 'Connected', 'message': 'Successfully connected', 'version': version}
            
        except CredentialError as e:
            error_msg = f"Authentication error connecting to {cb_instance.name}: {str(e)}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())
            cb_instance.update_connection_status('Authentication Failed', str(e))
            return {'status': 'Authentication Failed', 'message': error_msg, 'version': 'Unknown'}
            
        except ApiError as e:
            error_msg = f"API error connecting to {cb_instance.name}: {str(e)}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())
            cb_instance.update_connection_status('API Error', str(e))
            return {'status': 'API Error', 'message': error_msg, 'version': 'Unknown'}
            
        except Exception as e:
            error_msg = f"Error connecting to {cb_instance.name}: {str(e)}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())
            cb_instance.update_connection_status('Connection Error', str(e))
            return {'status': 'Connection Error', 'message': error_msg, 'version': 'Unknown'}
    
    @staticmethod
    def get_cb_api(cb_instance):
        """Get an initialized CB API client.
        
        Args:
            cb_instance: CBInstance model object
            
        Returns:
            CbResponseAPI or CbProtectionAPI: Initialized API client or None on error
        """
        try:
            logger.info(f"Initializing CB API client for {cb_instance.name} ({cb_instance.api_base_url})")
            credentials = cb_instance.to_credential_dict()
            
            if not credentials['url']:
                logger.error(f"Invalid URL for {cb_instance.name}: {credentials['url']}")
                return None
                
            if not credentials['token']:
                logger.error(f"Invalid API token for {cb_instance.name}")
                return None
            
            # We default to using Response API
            logger.info(f"Creating CbResponseAPI client for {cb_instance.name}")
            return CbResponseAPI(**credentials)
                
        except Exception as e:
            logger.error(f"Failed to initialize CB API for {cb_instance.name}: {str(e)}")
            logger.debug(traceback.format_exc())
            return None
    
    @staticmethod
    def sync_agents(cb_instance, db_session=None):
        """Sync agents/sensors from Carbon Black instance to database.
        
        Args:
            cb_instance: CBInstance model object
            db_session: Optional SQLAlchemy database session (if None, will use db.session)
            
        Returns:
            tuple: (success, count, message)
        """
        try:
            logger.info(f"Starting agent sync for {cb_instance.name}")
            
            # Use provided session or default to global db.session
            session = db_session or db.session
            
            cb_api = CBAPIHelper.get_cb_api(cb_instance)
            if not cb_api:
                error_msg = f"Failed to initialize CB API for {cb_instance.name}"
                logger.error(error_msg)
                return False, 0, error_msg
            
            count = 0
            
            # For Carbon Black Response (EDR) - our default server type
            logger.info(f"Syncing Response sensors for {cb_instance.name}")
            try:
                devices = cb_api.select(Sensor)
                
                for device in devices:
                    device_id = str(device.id)
                    
                    # Check if device exists in DB
                    agent = Agent.query.filter_by(id=device_id, instance_id=cb_instance.id).first()
                    
                    if not agent:
                        # Create new agent
                        logger.info(f"Creating new agent for sensor {device_id} - {getattr(device, 'hostname', 'unknown')}")
                        agent = Agent(
                            id=device_id,
                            instance_id=cb_instance.id,
                            hostname=getattr(device, 'hostname', 'Unknown'),
                            os=getattr(device, 'os_type', 'Unknown'),
                            version=getattr(device, 'build_version_string', 'Unknown'),
                            status=getattr(device, 'status', 'Unknown'),
                            groups=[]
                        )
                    else:
                        logger.debug(f"Updating existing agent for sensor {device_id} - {getattr(device, 'hostname', 'unknown')}")
                        # Update agent data
                        agent.hostname = getattr(device, 'hostname', 'Unknown')
                        agent.os = getattr(device, 'os_type', 'Unknown')
                        agent.version = getattr(device, 'build_version_string', 'Unknown')
                        agent.status = getattr(device, 'status', 'Unknown')
                        agent.last_check_in = getattr(device, 'last_checkin_time', None)
                    
                    # Add group if available
                    group_name = getattr(device, 'group_name', None)
                    if group_name and group_name not in agent.groups:
                        agent.groups.append(group_name)
                    
                    # Save agent to DB
                    session.add(agent)
                    count += 1
                    
            except Exception as device_err:
                logger.error(f"Error syncing devices: {str(device_err)}")
                logger.debug(traceback.format_exc())
                raise
            
            # Commit changes
            logger.info(f"Committing {count} agent updates for {cb_instance.name}")
            session.commit()
            
            # Update instance metadata
            cb_instance.sensors = count
            cb_instance.update_connection_status('Connected', f'Successfully synced {count} agents')
            logger.info(f"Successfully synced {count} agents for {cb_instance.name}")
            
            return True, count, f"Successfully synced {count} agents"
            
        except Exception as e:
            error_msg = f"Error syncing agents from {cb_instance.name}: {str(e)}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())
            return False, 0, error_msg 
    
    @staticmethod
    def get_users(cb_instance):
        """
        Get users from Carbon Black instance.
        
        Args:
            cb_instance: CBInstance model object
            
        Returns:
            list: List of user dictionaries
        """
        try:
            logger.info(f"Fetching users from {cb_instance.name}")
            
            # Get the CB API client
            cb_api = CBAPIHelper.get_cb_api(cb_instance)
            if not cb_api:
                error_msg = f"Failed to initialize CB API for {cb_instance.name}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            users = []
            
            # Get users based on server type
            if cb_instance.server_type.lower() == 'response':
                # For Carbon Black Response
                user_data = cb_api._request('GET', '/api/v1/users')
                if isinstance(user_data, list):
                    users = [
                        {
                            'id': user.get('id'),
                            'username': user.get('username'),
                            'email': user.get('email', ''),
                            'first_name': user.get('first_name', ''),
                            'last_name': user.get('last_name', ''),
                            'role': user.get('global_admin', False) and 'Admin' or 'User',
                            'status': user.get('enabled', True) and 'Active' or 'Disabled',
                            'last_login': user.get('last_login_time')
                        }
                        for user in user_data
                    ]
            
            else:  # 'protection'
                # For Carbon Black Protection
                user_data = cb_api._request('GET', '/api/bit9platform/v1/users')
                if isinstance(user_data, list):
                    users = [
                        {
                            'id': user.get('id'),
                            'username': user.get('name'),
                            'email': user.get('email', ''),
                            'first_name': '',  # Protection doesn't typically have separate first/last name
                            'last_name': '',
                            'role': user.get('userRole', {}).get('name', 'User'),
                            'status': user.get('enabled', True) and 'Active' or 'Disabled',
                            'last_login': user.get('lastAccessTime')
                        }
                        for user in user_data
                    ]
            
            logger.info(f"Retrieved {len(users)} users from {cb_instance.name}")
            return users
            
        except Exception as e:
            error_msg = f"Error retrieving users from {cb_instance.name}: {str(e)}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())
            raise Exception(error_msg)
    
    @staticmethod
    def import_instances_from_csv(csv_data, db_session=None):
        """Import Carbon Black instances from a CSV file.
        
        Expected CSV format:
        name,api_base_url,api_token
        Example CB,https://example.carbonblack.io,abcdef123456
        
        Args:
            csv_data: CSV data as string or file-like object
            db_session: Optional SQLAlchemy database session (if None, will use db.session)
            
        Returns:
            tuple: (success, count, message, failed_rows)
        """
        try:
            logger.info("Starting instance import from CSV")
            
            # Use provided session or default to global db.session
            from api.models import CBInstance
            session = db_session or db.session
            
            # If csv_data is a string, convert to file-like object
            if isinstance(csv_data, str):
                csv_data = io.StringIO(csv_data)
                
            csv_reader = csv.reader(csv_data)
            headers = next(csv_reader, None)
            
            # Validate headers
            expected_headers = ['name', 'api_base_url', 'api_token']
            if not headers or not all(header in headers for header in expected_headers):
                error_msg = f"Invalid CSV format. Expected headers: {', '.join(expected_headers)}"
                logger.error(error_msg)
                return False, 0, error_msg, []
                
            # Process rows
            count = 0
            failed_rows = []
            
            for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 to account for header row
                if len(row) < len(expected_headers):
                    failed_rows.append({
                        'row': row_num,
                        'data': row,
                        'error': 'Incomplete row data'
                    })
                    continue
                    
                # Map row to dict using headers
                row_data = dict(zip(headers, row))
                
                # Basic validation
                if not row_data.get('name') or not row_data.get('api_base_url') or not row_data.get('api_token'):
                    failed_rows.append({
                        'row': row_num,
                        'data': row_data,
                        'error': 'Missing required fields'
                    })
                    continue
                
                try:
                    # Generate a unique ID if not provided
                    instance_id = row_data.get('id', str(uuid.uuid4()))
                    
                    # Check if instance already exists
                    existing_instance = CBInstance.query.filter_by(id=instance_id).first()
                    if existing_instance:
                        failed_rows.append({
                            'row': row_num,
                            'data': row_data,
                            'error': f'Instance with ID {instance_id} already exists'
                        })
                        continue
                        
                    # Create new instance
                    new_instance = CBInstance(
                        id=instance_id,
                        name=row_data['name'],
                        api_base_url=row_data['api_base_url'],
                        api_token=row_data['api_token'],
                        is_active=row_data.get('is_active', 'true').lower() == 'true'
                    )
                    
                    # Add to session
                    session.add(new_instance)
                    count += 1
                    
                except Exception as instance_err:
                    logger.error(f"Error creating instance from row {row_num}: {str(instance_err)}")
                    failed_rows.append({
                        'row': row_num,
                        'data': row_data,
                        'error': str(instance_err)
                    })
            
            # Commit changes if any successful imports
            if count > 0:
                session.commit()
                
            result_msg = f"Successfully imported {count} instances"
            if failed_rows:
                result_msg += f" ({len(failed_rows)} failed)"
                
            logger.info(result_msg)
            return True, count, result_msg, failed_rows
            
        except Exception as e:
            error_msg = f"Error importing instances from CSV: {str(e)}"
            logger.error(error_msg)
            logger.debug(traceback.format_exc())
            return False, 0, error_msg, [] 