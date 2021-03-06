import boto3, os, sys, logging, glob

def main():

    FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(stream=sys.stdout, level=logging.INFO, format=FORMAT)
    logger = logging.getLogger(__name__)

    logger.info('Hello task - coming from test')

    # Run other commands
    logger.info(glob.glob('/*'))

    logger.info('Done - test')

if __name__ == '__main__':
    main()
