
const T = (x, d) => { 
    return x || d;
}

const img = "..."

const Finish = (props: { finishtext?: string, affImg?: any }) => {

    const t = props.finishtext ? T('finish.title', '') :
        T('finish.title2', '');

	return (
		<div className="login-profile__finish">
			<div className='affloading'>
				<img src={props.affImg || ''} />
				<div className="title">
					{props.finishtext || T("finish.welcome_message", 'Entering the jungle {ape_name}').replace('{ape_name}', 'Pippo')}
				</div>
				{props.affImg &&
					<>
						<div style={{ width: "80px", height: "100px", margin: 'auto' }} />
						<img src={img} />
                        {T('custom', '')}
					</>
				}
			</div>
		</div>
	);
};
