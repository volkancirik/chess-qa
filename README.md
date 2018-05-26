# chess-qa : Question-Answering Dataset on Chess Games

This is the repository for generation Q&A data for Chess Games. 

    @article{cirik2015chess,
      title={Chess QA: Question Answering on Chess Games},
      author={Cirik, Volkan and Morency, Louis-Philippe and Hovy, Eduard},
      journal={NIPS Reasoning, Attention, and Memory Workshop}, 
      year={2015},
    }


You need to install [python-chess 0.12.0](https://pypi.python.org/pypi/python-chess/0.12.0). I used the visualizer described [here](http://wordaligned.org/articles/drawing-chess-positions.html) to generate the images. For stalemate questions you need to use **data/stalemate.pgn** The code is extremely inefficent for now. Please contact me for further questions.

To see command line options:

    python generate_qa.py --help
  
  
  
TODO:

- write better README.md
- clean the code
- add baselines
