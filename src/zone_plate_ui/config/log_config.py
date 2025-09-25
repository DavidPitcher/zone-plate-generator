import logging.handlers
import sys
import logging
from loguru import logger
from zone_plate_ui.config.app_config import AppConfig
from zone_plate_ui.utils.log_messages import InterceptHandler, log

class LogConfig:
    @classmethod
    def init_app(cls, config: "AppConfig") -> None:
        """Initialize the Loguru configuration.
        
        Args:
            config: Configuration object containing logging attributes
                (LOG_LEVEL, LOG_BACKTRACE, LOG_SERIALIZE, LOG_QUEUE)
                
        Returns:
            None
        """
        
        try:
            # Remove Flask's default handler to prevent duplicate logging
            for handler in logging.root.handlers[:]:
                logging.root.removeHandler(handler)

            # Add the Loguru handler to the root logger
            logging.basicConfig(handlers=[InterceptHandler()], level=0)
           
            # Get log configuration attributes with safe defaults
            log_level = getattr(config, 'LOG_LEVEL', 'INFO')
            log_backtrace = getattr(config, 'LOG_BACKTRACE', False)
            log_serialize = getattr(config, 'LOG_SERIALIZE', False)
            log_queue = getattr(config, 'LOG_QUEUE', False)

            logger.remove()
            logger.add(
                sys.stderr, 
                format=log.log_format,
                colorize=True, 
                level=log_level,
                backtrace=log_backtrace,
                serialize=log_serialize,
                enqueue=log_queue
            )
    
            log.info(
                log.CFG_LOG_CONFIG_SUCCESS,
                level=log_level,
                backtrace=log_backtrace,
                serialize=log_serialize,
                enqueue=log_queue
            )


        except Exception as e:
            log.error(log.CFG_LOG_CONFIG_FAILURE, error=str(e))
            raise

