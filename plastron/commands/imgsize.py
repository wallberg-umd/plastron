import sys
from PIL import Image
from plastron import pcdm
from plastron.exceptions import FailureException
from plastron.util import RepositoryFile
from rdflib import URIRef
import logging

Image.MAX_IMAGE_PIXELS = None

logger = logging.getLogger(__name__)

class Command:
    def __init__(self, subparsers):
        parser = subparsers.add_parser('imgsize',
                description='Add width and height to image resources')
        parser.add_argument('uris', nargs='*',
                            help='URIs of repository objects to get image info'
                            )
        parser.set_defaults(cmd_name='imgsize')

    def __call__(self, fcrepo, args):
        for uri in args.uris:
            source = RepositoryFile(fcrepo, uri)
            if source.mimetype().startswith('image/'):
                logger.info(f'Reading image data from {uri}')

                file = pcdm.File(source)
                image = Image.open(source.data())

                logger.info(f'URI: {uri}, Width: {image.width}, Height: {image.height}')

                # construct SPARQL query to replace image size metadata
                prolog = 'PREFIX ebucore: <http://www.ebu.ch/metadata/ontologies/ebucore/ebucore#>'
                delete = 'DELETE { <> ebucore:width ?w ; ebucore:height ?h }'
                statements = f'<> ebucore:width {image.width} ; ebucore:height {image.height}'
                insert = 'INSERT { ' + statements + ' }'
                where = 'WHERE {}'
                sparql = '\n'.join((prolog, delete, insert, where))

                # update the metadata
                headers = {'Content-Type': 'application/sparql-update'}
                response = fcrepo.patch(source.metadata_uri, data=sparql, headers=headers)
                if response.status_code == 204:
                    logger.info(f'Updated image dimensions on {uri}')
                else:
                    logger.warn(f'Unable to update {uri}')

            else:
                logger.warn(f'{uri} is not of type image/*; skipping')